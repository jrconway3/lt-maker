from app.data.constants import TILEWIDTH, TILEHEIGHT, COLORKEY
from app.data.palettes import gray_colors, enemy_colors, other_colors, enemy2_colors

from app.data.resources import RESOURCES
from app.data.database import DB

from app.engine import engine
from app.engine.game_state import game

def color_convert(image, conversion_dict):
    image = image.convert()
    px_array = engine.make_pixel_array(image)
    for old_color, new_color in conversion_dict.items():
        px_array.replace(old_color, new_color)
    px_array.close()
    return image

class MapSprite():
    def __init__(self, map_sprite, team):
        self.nid = map_sprite.nid
        self.team = team
        self.resource = map_sprite
        if not map_sprite.standing_image:
            map_sprite.standing_image = engine.image_load(map_sprite.standing_full_path)
            gray_stand = map_sprite.standing_image.copy()
        if not map_sprite.moving_image:
            map_sprite.moving_image = engine.image_load(map_sprite.moving_full_path)
        stand, move = self.convert_to_team_colors(map_sprite)
        engine.set_colorkey(stand, COLORKEY, rleaccel=True)
        engine.set_colorkey(move, COLORKEY, rleaccel=True)
        self.passive = [engine.subsurface(stand, (num*64, 0, 64, 48)) for num in range(3)]
        self.gray = self.create_gray([engine.subsurface(gray_stand, (num*64, 0, 64, 48)) for num in range(3)])
        self.active = [engine.subsurface(stand, (num*64, 96, 64, 48)) for num in range(3)]
        self.down = [engine.subsurface(move, (num*48, 0, 48, 40)) for num in range(4)]
        self.left = [engine.subsurface(move, (num*48, 40, 48, 40)) for num in range(4)]
        self.right = [engine.subsurface(move, (num*48, 80, 48, 40)) for num in range(4)]
        self.up = [engine.subsurface(move, (num*48, 120, 48, 40)) for num in range(4)]

    def convert_to_team_colors(self, map_sprite):
        if self.team == 'player':
            return map_sprite.standing_image, map_sprite.moving_image
        elif self.team == 'enemy':
            conversion_dict = enemy_colors
        elif self.team == 'enemy2':
            conversion_dict = enemy2_colors
        elif self.team == 'other':
            conversion_dict = other_colors

        return color_convert(map_sprite.standing_image, conversion_dict), \
            color_convert(map_sprite.moving_image, conversion_dict)

    def create_gray(self, imgs):
        imgs = []
        for img in imgs:
            imgs.append(color_convert(img, gray_colors))
        return imgs

class UnitSprite():
    def __init__(self, unit):
        self.unit = unit
        self.state = 'normal'  # What state the image sprite is in
        self.image_state = 'passive'  # What the image looks like
        self.transition_state = 'normal'

        self.transition_counter = 0
        self.transition_time = 400

        self.next_position = None
        self.offset = [0, 0]

        self.load_sprites()

    def load_sprites(self):
        klass = DB.classes.get(self.unit.klass)
        gender = self.unit.gender
        if gender >= 5 and klass.female_map_sprite_nid:
            res = RESOURCES.map_sprites.get(klass.female_map_sprite_nid)
        else:
            res = RESOURCES.map_sprites.get(klass.male_map_sprite_nid)
        if res:
            team = self.unit.team
            map_sprite = game.map_sprite_registry.get(res.nid + '_' + team)
            if not map_sprite:
                map_sprite = MapSprite(res, team)
                game.map_sprite_registry[map_sprite.nid + '_' + team] = map_sprite
            self.map_sprite = map_sprite
        else:
            self.map_sprite = None

    # Normally drawing units is culled to those on the screen
    # Unit sprites matching this will be drawn anyway
    def draw_anyway(self):
        return self.transition_state != 'normal'

    def set_transition(self, new_state):
        self.transition_state = new_state
        if self.transition_state == 'fake_in':
            self.change_state('fake_transition_in')
        elif self.transition_state in ('fake_out', 'rescue'):
            self.change_state('fake_transition_out')

    def change_state(self, new_state):
        self.state = new_state

    def update(self):
        self.update_state()
        self.update_transition()

    def update_state(self):
        if self.state == 'normal':
            if self.unit.finished and not self.unit.is_dying:
                self.image_state = 'gray'
            elif game.cursor.draw_state and game.cursor.position == self.unit.position and self.unit.team == 'player':
                self.image_state = 'active'
            else:
                self.image_state = 'passive'

    def update_transition(self):
        pass

    def select_frame(self, image):
        if self.image_state == 'passive' or self.image_state == 'gray':
            return image[game.map_view.passive_sprite_counter.count].copy()
        elif self.image_state == 'active':
            return image[game.map_view.active_sprite_counter.count].copy()
        elif self.state == 'combat_anim':
            return image[game.map_view.fast_move_sprite_counter].copy()
        else:
            return image[game.map_view.move_sprite_counter].copy()

    def draw(self, surf):
        image = getattr(self.map_sprite, self.image_state)
        image = self.select_frame(image)
        x, y = self.unit.position
        left = x * TILEWIDTH + self.offset[0]
        top = y * TILEHEIGHT + self.offset[1]

        # Each image has (self.image.get_width() - 32)//2 buggers on the
        # left and right of it, to handle any off tile spriting
        topleft = left - max(0, (image.get_width() - 16)//2), top - 24
        surf.blit(image, topleft)
        return surf
