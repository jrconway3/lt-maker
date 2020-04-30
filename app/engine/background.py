from app.engine import engine, image_mods

class SpriteBackground():
    def __init__(self, image, fade=True):
        self.counter = 0
        self.image = image

        if fade:
            self.fade = 100
            self.state = "in"
        else:
            self.fade = 0
            self.state = "normal"

    def draw(self, surf):
        if self.state == "in":
            self.fade -= 4
            if self.fade <= 0:
                self.fade = 0
                self.state = "normal"
            bg_surf = image_mods.make_translucent(self.image, self.fade/100.)
        elif self.state == "out":
            self.fade += 4
            bg_surf = image_mods.make_translucent(self.image, self.fade/100.)
            if self.fade >= 100:
                return True
        else:
            bg_surf = self.image

        engine.blit_center(surf, bg_surf)
        return False

    def fade_out(self):
        self.state = 'out'

class PanoramaBackground():
    def __init__(self, panorama, speed=125, loop=True, fade_out=False):
        self.counter = 0
        self.panorama = panorama
        if not self.panorama.images:
            for path in self.panorama.get_all_paths():
                self.panorama.images.append(engine.image_load(path))

        self.speed = speed
        self.loop = loop
        self.fade_out = fade_out

        self.last_update = engine.get_time()

    def draw(self, surf):
        image = self.panorama.get_img_frame()
        if image:
            engine.blit_center(surf, image)

        if engine.get_time() - self.last_update > self.speed:
            self.panorama.increment_frame()
            self.last_update = engine.get_time()
            if self.panorama.idx == 0 and not self.loop:
                return True
        return False
