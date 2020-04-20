from app.data.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT, FRAMERATE
from app.data.resources import RESOURCES

from app.counters import generic3counter, simple4counter

from app.engine import engine, unit_sprite
from app.engine.game_state import game

class MapView():
    def __init__(self, tilemap):
        self.tilemap = tilemap
        map_full_path = RESOURCES.maps.get(self.tilemap.base_image_nid).full_path
        self.map_image = engine.image_load(map_full_path)

        self.passive_sprite_counter = generic3counter(32 * FRAMERATE, 4 * FRAMERATE)
        self.active_sprite_counter = generic3counter(13 * FRAMERATE, 6 * FRAMERATE)
        self.move_sprite_counter = simple4counter((10 * FRAMERATE, 5 * FRAMERATE, 10 * FRAMERATE, 5 * FRAMERATE))
        self.fast_move_sprite_counter = simple4counter((6 * FRAMERATE, 3 * FRAMERATE, 6 * FRAMERATE, 3 * FRAMERATE))

    def update(self):
        current_time = engine.get_time()
        self.passive_sprite_counter.update(current_time)
        self.active_sprite_counter.update(current_time)
        self.move_sprite_counter.update(current_time)
        self.fast_move_sprite_counter.update(current_time)

    def draw_units(self, surf):
        culled_units = [unit for unit in game.level.units if unit.position]
        draw_units = sorted(culled_units, key=lambda unit: unit.position[1])
        for unit in draw_units:
            if not unit.sprite:
                unit.sprite = unit_sprite.UnitSprite(unit)
            unit.sprite.update()
            surf = unit.sprite.draw(surf)

    def draw(self):
        surf = engine.copy_surface(self.map_image)
        surf = surf.convert_alpha()
        surf = game.highlight.draw(surf)
        surf = game.cursor.draw_arrows(surf)
        self.draw_units(surf)
        surf = game.cursor.draw(surf)

        # Cull
        rect = game.camera.get_x() * TILEWIDTH, game.camera.get_y() * TILEHEIGHT, WINWIDTH, WINHEIGHT
        surf = engine.subsurface(surf, rect)
        return surf
