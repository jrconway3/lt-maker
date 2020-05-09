from app.data.constants import WINWIDTH, WINHEIGHT
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

class TransitionBackground():
    speed = 25
    fade_speed = 4

    def __init__(self, image, fade=True):
        self.counter = 0
        self.image = image

        self.last_update = engine.get_time()
        self.width = image.get_width()
        self.height = image.get_height()

        if self.fade:
            self.fade = 100
            self.state = 'in'
        else:
            self.fade = 0
            self.state = 'normal'

    def update(self):
        current_time = engine.get_time()
        diff = current_time - self.last_update
        self.counter += diff / self.speed
        self.counter %= self.width
        self.last_update = current_time

        if self.state == 'in':
            self.fade -= current_time / self.fade_speed
            if self.fade <= 0:
                self.fade = 0
                self.state = 'normal'

    def draw(self, surf):
        xindex = -self.counter
        while xindex < WINWIDTH:
            yindex = -self.counter
            while yindex < WINHEIGHT:
                # left = self.counter if xindex < 0 else 0
                # top = self.counter if yindex < 0 else 0
                # if xindex > WINWIDTH:
                #     right = self.width - utilities.clamp((xindex + self.width - WINWIDTH), 0, self.width)
                # else:
                #     right = self.width
                # if yindex > WINHEIGHT:
                #     top = self.height - utilities.clamp((yindex + self.height - WINHEIGHT), 0, self.height)
                # else:
                #     top = self.height
                # surf = engine.subsurface(self.image, (left, top, right - left, bottom - top))
                image = self.image
                if self.fade:
                    image = image_mods.make_translucent(image, self.fade / 100.)
                surf.blit(image, (xindex, yindex))
                yindex += self.height
            xindex += self.width