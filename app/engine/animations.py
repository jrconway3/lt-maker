from app import utilities
from app.data.constants import TILEWIDTH, TILEHEIGHT

from app.engine import engine

# Generic Animation Object
# Used, for instance, for miss and no damage animations

class Animation():
    def __init__(self, anim, position, delay=0, loop=0, hold=False):
        if not anim.sprite:
            anim.sprite = engine.image_load(anim.full_path)
        self.sprite = anim.sprite
        self.position = position
        self.frame_x, self.frame_y = anim.frame_x, anim.frame_y
        self.num_frames = anim.num_frames
        self.speed = anim.speed
        self.delay = delay
        self.loop = loop
        self.hold = hold
        self.enabled = True
        self.tint = False

        self.width = self.sprite.get_width() // self.frame_x
        self.height = self.sprite.get_height() // self.frame_y

        self.image = engine.subsurface(self.sprite, (0, 0, self.width, self.height))

        self.counter = 0
        self.first_update = engine.get_time()

    def use_center(self):
        self.position = self.position[0] - self.width//2, self.position[1] - self.height//2

    def is_ready(self, current_time):
        return self.enabled and (current_time - self.first_update >= self.delay)

    def update(self):
        current_time = engine.get_time()
        if not self.is_ready(current_time):
            return

        done = False
        if utilities.is_int(self.speed):
            self.counter = int(current_time - self.first_update) // self.speed
            if self.counter >= self.num_frames:
                if self.loop:
                    self.counter = 0
                    self.first_update = int(current_time - self.first_update) % self.speed
                    self.delay = 0
                elif self.hold:
                    self.counter = self.num_frames - 1
                else:
                    self.counter = self.num_frames - 1
                    done = True

        # Now actually create image
        left = (self.counter % self.frame_x) * self.width
        top = (self.counter // self.frame_x) * self.height
        self.image = engine.subsurface(self.sprite, (left, top, self.width, self.height))

        return done

    def draw(self, surf):
        current_time = engine.get_time()
        if not self.is_ready(current_time):
            return surf
        x, y = self.position
        surf.blit(self.image, (x, y))
        return surf

class MapAnimation(Animation):
    def __init__(self, anim, position, speed=75, delay=0, loop=0, hold=False):
        super().__init__(anim, position, speed, delay, loop, hold)
        self.position = self.position[0] * TILEWIDTH, self.position[1] * TILEHEIGHT
        self.use_center()

    def use_center(self):
        self.position = self.position[0] + TILEWIDTH//2 - self.width//2, self.position[1] + TILEHEIGHT//2 - self.height//2
