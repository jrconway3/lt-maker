from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FPS, AUTOTILE_FRAMES
from app.utilities.data import Data, Prefab

from app.resources.resources import RESOURCES

from app.engine import engine, image_mods, particles

class LayerObject():
    transition_speed = 333

    def __init__(self, nid: str, parent):
        self.nid: str = nid
        self.parent = parent
        self.visible = True
        self.terrain = {}
        self.image = None
        self.autotile_images = []

        # For fade in
        self.state = None
        self.translucence = 1
        self.start_update = 0
        self.autotile_frame = 0

    def set_image(self, image):
        self.image = image

    def get_image(self):
        if self.state in ('fade_in', 'fade_out'):
            return image_mods.make_translucent(self.image, self.translucence)
        return self.image

    def get_autotile_image(self):
        im = self.autotile_images[self.autotile_frame]
        if self.state in ('fade_in', 'fade_out'):
            return image_mods.make_translucent(im, self.translucence)
        return im

    def quick_show(self):
        self.visible = True

    def quick_hide(self):
        self.visible = False

    def show(self):
        """
        Fades in the layer
        """
        if not self.visible:
            self.visible = True
            self.state = 'fade_in'
            self.translucence = 1
            self.start_update = engine.get_time()

    def hide(self):
        """
        Fades out the layer
        """
        if self.visible:
            self.visible = False
            self.state = 'fade_out'
            self.translucence = 0
            self.start_update = engine.get_time()

    def update(self) -> bool:
        current_time = engine.get_time()
        in_state = bool(self.state)

        if self.state == 'fade_in':
            self.translucence = 1 - (current_time - self.start_update)/self.transition_speed
            if self.translucence <= 0:
                self.state = None
        elif self.state == 'fade_out':
            self.translucence = (current_time - self.start_update)/self.transition_speed
            if self.translucence >= 1:
                self.state = None

        frame = (current_time // AUTOTILE_FPS) % len(self.autotile_images)
        if frame != self.autotile_frame:
            self.autotile_frame = frame
            in_state = True  # Requires update to image when autotiles turn over

        return in_state

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['visible'] = self.visible
        return s_dict

    # Restore not needed -- handled in TileMapObjects deserialize function

class TileMapObject(Prefab):
    @classmethod
    def from_prefab(cls, prefab):
        self = cls()
        self.nid = prefab.nid
        self.width = prefab.width
        self.height = prefab.height
        self.layers = Data()
        self.full_image = None

        # Stitch together image layers
        for layer in prefab.layers:
            new_layer = LayerObject(layer.nid, self)
            # Terrain
            for coord, terrain_nid in layer.terrain_grid.items():
                new_layer.terrain[coord] = terrain_nid
            # Image
            image = engine.create_surface((self.width * TILEWIDTH, self.height * TILEHEIGHT), transparent=True)
            # Autotile Images
            autotile_images = [engine.create_surface((self.width * TILEWIDTH, self.height * TILEHEIGHT), transparent=True) for _ in range(AUTOTILE_FRAMES)]

            for coord, tile_sprite in layer.sprite_grid.items():
                tileset = RESOURCES.tilesets.get(tile_sprite.tileset_nid)
                if not tileset.image:
                    tileset.image = engine.image_load(tileset.full_path)
                if not tileset.autotile_image and tileset.autotile_full_path:
                    tileset.autotile_image = engine.image_load(tileset.autotile_full_path)
                pos = tile_sprite.tileset_position
    
                rect = (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                sub_image = engine.subsurface(tileset.image, rect)
                image.blit(sub_image, (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT))

                # Handle Autotiles
                if pos in tileset.autotiles and tileset.autotile_image:
                    column = tileset.autotiles[pos]
                    for idx, im in enumerate(autotile_images):
                        rect = (column * TILEWIDTH, idx * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                        sub_image = engine.subsurface(tileset.autotile_image, rect)
                        im.blit(sub_image, (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT))

            new_layer.image = image
            new_layer.autotile_images = autotile_images
            self.layers.append(new_layer)

        # Base layer should be visible, rest invisible
        for layer in self.layers:
            layer.visible = False
        self.layers.get('base').visible = True

        self.weather = []

        return self

    def check_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def on_border(self, pos):
        return pos[0] == 0 or pos[1] == 0 or pos[0] == self.width - 1 or pos[1] == self.height - 1

    def get_terrain(self, pos):
        for layer in reversed(self.layers):
            if layer.visible and pos in layer.terrain:
                return layer.terrain[pos]
        return '0'

    def get_layer(self, pos):
        for layer in reversed(self.layers):
            if layer.visible and pos in layer.terrain:
                return layer.nid
        return None

    def get_full_image(self):
        if not self.full_image:
            image = engine.create_surface((self.width * TILEWIDTH, self.height * TILEHEIGHT), transparent=True)
            for layer in self.layers:
                if layer.visible or layer.state == 'fade_out':
                    image.blit(layer.get_image(), (0, 0))
                    image.blit(layer.get_autotile_image(), (0, 0))
            self.full_image = image
        return self.full_image

    def update(self):
        for layer in self.layers:
            in_state = layer.update()
            if in_state:
                self.reset()

    def reset(self):
        self.full_image = None

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['layers'] = [layer.save() for layer in self.layers]
        s_dict['weather'] = [weather.save() for weather in self.weather]
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        prefab = RESOURCES.tilemaps.get(s_dict['nid'])
        self = cls.from_prefab(prefab)
        self.restore_layers(s_dict['layers'])
        weather = s_dict.get('weather', [])
        self.weather = [particles.create_system(nid, self.width, self.height) for nid in weather]
        return self

    def restore_layers(self, layer_list):
        for layer_dict in layer_list:
            nid = layer_dict['nid']
            visible = layer_dict['visible']
            self.layers.get(nid).visible = visible
