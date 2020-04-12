from app.engine import engine

class Background():
    def __init__(self, panorama, speed=125, loop=True, fade_out=False):
        self.counter = 0
        self.panorama = panorama
        if not self.panorama.pixmaps:
            for path in self.panorama.get_all_paths():
                self.panorama.pixmaps.append(engine.image_load(path))

        self.speed = speed
        self.loop = loop
        self.fade_out = fade_out

        self.last_update = engine.get_time()

    def draw(self, surf):
        image = self.panorama.get_frame()
        engine.blit_center(surf, image)

        if engine.get_time() - self.last_update > self.speed:
            self.panorama.increment_frame()
            self.last_update = engine.get_time()
            if self.panorama.idx == 0 and not self.loop:
                return 'Done'
