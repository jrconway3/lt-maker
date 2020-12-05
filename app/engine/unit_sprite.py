from app.constants import TILEWIDTH, TILEHEIGHT, COLORKEY
from app.data.palettes import gray_colors, enemy_colors, other_colors, enemy2_colors

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.utilities import utils

from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine import engine, image_mods, health_bar, equations
import app.engine.config as cf
from app.engine.game_state import game

class MapSprite():
    def __init__(self, map_sprite, team):
        self.nid = map_sprite.nid
        self.team = team
        self.resource = map_sprite
        if not map_sprite.standing_image:
            map_sprite.standing_image = engine.image_load(map_sprite.stand_full_path)
        gray_stand = map_sprite.standing_image.copy()
        if not map_sprite.moving_image:
            map_sprite.moving_image = engine.image_load(map_sprite.move_full_path)
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

        return image_mods.color_convert(map_sprite.standing_image, conversion_dict), \
            image_mods.color_convert(map_sprite.moving_image, conversion_dict)

    def create_gray(self, imgs):
        imgs = [image_mods.color_convert(img, gray_colors) for img in imgs]
        for img in imgs:
            engine.set_colorkey(img, COLORKEY, rleaccel=True)
        return imgs

class UnitSprite():
    def __init__(self, unit):
        self.unit = unit
        self.state = 'normal'  # What state the image sprite is in
        self.image_state = 'passive'  # What the image looks like
        self.transition_state = 'normal'

        self.transition_counter = 0
        self.transition_time = 450

        self.fake_position = None  # For escape and rescue, etc...
        self.net_position = None
        self.offset = [0, 0]

        self.flicker = []
        self.vibrate = []
        self.vibrate_counter = 0

        self.load_sprites()

        self.health_bar = health_bar.MapHealthBar(self.unit)

    def load_sprites(self):
        klass = DB.classes.get(self.unit.klass)
        nid = klass.map_sprite_nid
        if self.unit.variant:
            nid += self.unit.variant
        res = RESOURCES.map_sprites.get(nid)
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

    def reset(self):
        self.offset = [0, 0]
        game.map_view.attack_movement_counter.reset()

    def begin_flicker(self, total_time, color):
        self.flicker.append((engine.get_time(), total_time, color, False))

    def start_flicker(self, start_time, total_time, color, fade_out=False):
        self.flicker.append((engine.get_time() + start_time, total_time, color, fade_out))

    def start_vibrate(self, start_time, total_time):
        self.vibrate.append((engine.get_time() + start_time, total_time))

    def set_transition(self, new_state):
        self.transition_state = new_state
        self.transition_counter = self.transition_time  # 450

        if self.transition_state == 'normal':
            self.offset = [0, 0]
            self.fake_position = None
        elif self.transition_state == 'fake_in':
            self.fake_position = None
            self.change_state('fake_transition_in')
        elif self.transition_state in ('fake_out', 'rescue'):
            self.fake_position = self.unit.position
            self.change_state('fake_transition_out')
        elif self.transition_state == 'fade_in':
            self.fake_position = None
        elif self.transition_state == 'fade_out':
            self.fake_position = self.unit.position
        elif self.transition_state == 'fade_move':
            self.fake_position = self.unit.position
        elif self.transition_state == 'warp_in':
            SOUNDTHREAD.play_sfx('WarpEnd')
        elif self.transition_state == 'warp_out':
            SOUNDTHREAD.play_sfx('Warp')
            self.fake_position = self.unit.position
        elif self.transition_state == 'warp_move':
            SOUNDTHREAD.play_sfx('Warp')
            self.fake_position = self.unit.position

    def change_state(self, new_state):
        self.state = new_state
        if self.state in ('combat_attacker', 'combat_anim'):
            self.net_position = game.cursor.position[0] - self.unit.position[0], game.cursor.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
            self.reset()
        elif self.state in ('combat_active'):
            self.image_state = 'active'
        elif self.state == 'combat_defender':
            attacker = game.combat_instance.attacker
            self.net_position = attacker.position[0] - self.unit.position[0], attacker.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'combat_counter':
            attacker = game.combat_instance.defender
            self.net_position = attacker.position[0] - self.unit.position[0], attacker.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_in':
            pos = (self.unit.position[0] + utils.clamp(self.offset[0], -1, 1),
                   self.unit.position[1] + utils.clamp(self.offset[1], -1, 1))
            pos = (pos[0] - self.unit.position[0], pos[1] - self.unit.position[1])
            self.net_position = (-pos[0], -pos[1])
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_out':
            pos = (utils.clamp(self.offset[0], -1, 1),
                   utils.clamp(self.offset[1], -1, 1))
            self.net_position = pos
            self.handle_net_position(self.net_position)
        elif self.state == 'selected':
            self.image_state = 'down'

    def handle_net_position(self, pos):
        if abs(pos[0]) >= abs(pos[1]):
            if pos[0] > 0:
                self.image_state = 'right'
            elif pos[0] < 0:
                self.image_state = 'left'
            else:
                self.image_state = 'down'  # default
        else:
            if pos[1] < 0:
                self.image_state = 'up'
            else:
                self.image_state = 'down'

    def update(self):
        self.update_state()
        self.update_transition()
        self.health_bar.update()

    def update_state(self):
        current_time = engine.get_time()
        if self.state == 'normal':
            if self.unit.finished and not self.unit.is_dying:
                self.image_state = 'gray'
            elif game.cursor.draw_state and game.cursor.position == self.unit.position and self.unit.team == 'player':
                self.image_state = 'active'
            else:
                self.image_state = 'passive'
        elif self.state == 'combat_anim':
            self.offset[0] = utils.clamp(self.net_position[0], -1, 1) * game.map_view.attack_movement_counter.value()
            self.offset[1] = utils.clamp(self.net_position[1], -1, 1) * game.map_view.attack_movement_counter.value()
        elif self.state == 'chosen':
            self.net_position = game.cursor.position[0] - self.unit.position[0], game.cursor.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'moving':
            next_position = game.moving_units.get_next_position(self.unit.nid)
            if not next_position:
                self.set_transition('normal')
                return
            self.net_position = (next_position[0] - self.unit.position[0], next_position[1] - self.unit.position[1])
            last_update = game.moving_units.get_last_update(self.unit.nid)
            dt = current_time - last_update
            self.offset[0] = int(TILEWIDTH * dt / cf.SETTINGS['unit_speed'] * self.net_position[0])
            self.offset[1] = int(TILEHEIGHT * dt / cf.SETTINGS['unit_speed'] * self.net_position[1])
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_in':
            if self.offset[0] > 0:
                self.offset[0] -= 2
            elif self.offset[0] < 0:
                self.offset[0] += 2
            if self.offset[1] > 0:
                self.offset[1] -= 2
            elif self.offset[1] < 0:
                self.offset[1] += 2

            if self.offset[0] == 0 and self.offset[1] == 0:
                self.set_transition('normal')
                self.change_state('normal')
        elif self.state == 'fake_transition_out':
            if self.offset[0] > 0:
                self.offset[0] += 2
            elif self.offset[0] < 0:
                self.offset[0] -= 2
            if self.offset[1] > 0:
                self.offset[1] += 2
            elif self.offset[1] < 0:
                self.offset[1] -= 2

            if abs(self.offset[0]) > TILEWIDTH or abs(self.offset[1]) > TILEHEIGHT:
                self.set_transition('normal')
                self.change_state('normal')

    def update_transition(self):
        self.transition_counter -= engine.get_delta()
        if self.transition_counter < 0:
            self.transition_counter = 0
            self.fake_position = None
            if self.transition_state in ('fade_out', 'warp_out', 'fade_in', 'warp_in'):
                self.set_transition('normal')
            elif self.transition_state == 'fade_move':
                self.set_transition('fade_in')
            elif self.transition_state == 'warp_move':
                self.set_transition('warp_in')

    def select_frame(self, image):
        if self.unit.is_dying:
            return image[0].copy()
        elif self.image_state == 'passive' or self.image_state == 'gray':
            return image[game.map_view.passive_sprite_counter.count].copy()
        elif self.image_state == 'active':
            return image[game.map_view.active_sprite_counter.count].copy()
        elif self.state == 'combat_anim':
            return image[game.map_view.fast_move_sprite_counter.count].copy()
        else:
            return image[game.map_view.move_sprite_counter.count].copy()

    def create_image(self, state):
        image = getattr(self.map_sprite, state)
        image = self.select_frame(image)
        return image

    def draw(self, surf):
        image = self.create_image(self.image_state)
        if self.fake_position:
            x, y = self.fake_position
        elif self.unit.position:
            x, y = self.unit.position
        left = x * TILEWIDTH + self.offset[0]
        top = y * TILEHEIGHT + self.offset[1]

        self.vibrate_counter += 1
        for vibrate in self.vibrate[:]:
            starting_time, total_time = vibrate
            if engine.get_time() >= starting_time:
                if engine.get_time() > starting_time + total_time:
                    self.vibrate.remove(vibrate)
                    continue
                left += (1 if self.vibrate_counter % 2 else -1)

        # Handle transitions
        if self.transition_state in ('fade_out', 'warp_out', 'fade_move', 'warp_move'):
            progress = utils.clamp((self.transition_time - self.transition_counter) / self.transition_time, 0, 1)
            image = image_mods.make_translucent(image.convert_alpha(), progress)
        elif self.transition_state in ('fade_in', 'warp_in'):
            progress = utils.clamp((self.transition_time - self.transition_counter) / self.transition_time, 0, 1)
            progress = 1 - progress
            image = image_mods.make_translucent(image.convert_alpha(), progress)

        for flicker in self.flicker[:]:
            starting_time, total_time, color, fade_out = flicker
            if engine.get_time() >= starting_time:
                if engine.get_time() > starting_time + total_time:
                    self.flicker.remove(flicker)
                    continue
                if fade_out:
                    time_passed = engine.get_time() - starting_time
                    color = tuple((total_time - time_passed) * float(c) // total_time for c in color)
                image = image_mods.change_color(image.convert_alpha(), color)

        if not self.flicker and game.boundary.draw_flag and self.unit in game.boundary.displaying_units:
            image = image_mods.change_color(image.convert_color, (80, 0, 0))

        if game.action_log.hovered_unit is self.unit:
            time = engine.get_time()
            length = 200
            if not (time // length) % 2:
                diff = time % length
                if diff > length // 2:
                    diff = length - diff
                diff = utils.clamp(255. * diff / length * 2, 0, 255) 
                color = (-120, 120, -120, diff)  # Tint image green at magnitude depending on diff
                image = image_mods.tint_image(image.convert_alpha(), color)

        # Each image has (self.image.get_width() - 32)//2 buggers on the
        # left and right of it, to handle any off tile spriting
        topleft = left - max(0, (image.get_width() - 16)//2), top - 24
        surf.blit(image, topleft)

        cur_unit = game.cursor.get_hover()
        if cur_unit:
            if (cur_unit.nid, self.unit.nid) in game.talk_options:
                frame = (engine.get_time() // 100) % 8
                topleft = (left - 2, top - 14)
                offset = [0, 0, 0, 1, 2, 2, 2, 1][frame]
                surf.blit(SPRITES.get('talk_marker'), (topleft[0], topleft[1] + offset))
                
        return surf

    def check_draw_hp(self) -> bool:
        if self.unit.is_dying:
            return False
        if (cf.SETTINGS['hp_map_team'] == 'All') or \
           (cf.SETTINGS['hp_map_team'] == 'Ally' and self.unit.team in ('player', 'other')) or \
           (cf.SETTINGS['hp_map_team'] == 'Enemy' and self.unit.team.startswith('enemy')):
            if (cf.SETTINGS['hp_map_cull'] == 'All') or \
               (cf.SETTINGS['hp_map_cull'] == 'Wounded' and self.unit.get_hp() < equations.parser.hitpoints(self.unit)):
                return True
        return False

    def draw_hp(self, surf):
        current_time = engine.get_time()
        if self.fake_position:
            x, y = self.fake_position
        elif self.unit.position:
            x, y = self.unit.position
        left = x * TILEWIDTH + self.offset[0]
        top = y * TILEHEIGHT + self.offset[1]

        if self.check_draw_hp():
            self.health_bar.draw(surf, left, top)

        if 'Boss' in self.unit.tags and self.transition_state == 'normal' and not self.unit.is_dying and \
                self.image_state in ('gray', 'passive') and int((current_time%450) // 150) in (1, 2):
            boss_icon = SPRITES.get('boss_icon')
            surf.blit(boss_icon, (left - 8, top - 8))

        if self.unit.traveler and self.transition_state == 'normal' and not self.unit.is_dying:
            if game.level.units.get(self.unit.traveler).team == 'player':
                rescue_icon = SPRITES.get('rescue_icon_blue')
            else:
                rescue_icon = SPRITES.get('rescue_icon_green')
            topleft = (left - 8, top - 8)
            surf.blit(rescue_icon, topleft)

        return surf
