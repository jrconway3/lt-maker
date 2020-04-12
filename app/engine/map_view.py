from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.data.resources import RESOURCES

from app.engine import engine
from app.engine.game_state import game

class MapView():
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.map_image = RESOURCES.maps.get(self.tilemap.base_image_nid)
        self.map_image = engine.image_load(self.map_image)

    def draw_units(self, surf):
        for unit in game.level.units:
            if unit.position:
                pass

    def draw(self):
        surf = engine.copy_surface(self.map_image)
        self.draw_units(surf)
        game.cursor.draw(surf)
        rect = game.camera.get_x() * TILEWIDTH, game.camera.get_y() * TILEHEIGHT
        surf = engine.subsurface(surf, rect)
        return surf
