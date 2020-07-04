import math
from app import counters
from app.engine.sprites import SPRITES
from app.engine import engine, image_mods

class DamageNumber():
    time_bounce = 400
    time_pause = 600
    time_total = 1200

    def __init__(self, num, idx, length, left, color):
        image = SPRITES.get('damage_numbers_' + color)
        if color.startswith('small'):
            self.small = True
        else:
            self.small = False

        self.num = num
        self.idx = idx
        self.length = length
        self.left = left
        self.true_image = engine.subsurface(image, (num*16, 0, 16, 16))
        self.image = None
        self.done = False
        self.start_time = engine.get_time()
        self.top_pos = 0
        self.state = -1
        if self.small:
            self.init_time = 50 * self.idx
        else:
            self.init_time = 50 * self.idx + 50

    def update(self):
        new_time = float(engine.get_time() - self.start_time)
        # Totally transparent start_up
        if self.state == -1:
            if new_time > self.init_time:
                self.state = 0
        # Initial bouncing and fading in
        if self.state == 0:
            state_time = new_time - self.init_time
            # Position
            self.top_pos = 10 * math.exp(-state_time/250) * math.sin(state_time/25)
            # Transparency
            new_transparency = (200 - state_time)/200.  # First 200 milliseconds of transparency
            self.image = image_mods.make_translucent(self.true_image, new_transparency)
            if state_time > self.time_bounce:
                self.state = 1
                self.top_pos = 0
        # Pause
        if self.state == 1:
            if new_time > self.init_time + self.time_bounce + self.time_pause:
                self.state = 2
        # Fade out and up
        if self.state == 2:
            state_time = new_time - self.init_time - self.time_bounce - self.time_pause
            # Position
            self.top_pos = state_time/10
            # Transparency
            new_transparency = state_time/150
            self.image = image_mods.make_translucent(self.true_image, new_transparency)
            if new_time > self.time_total:
                self.done = True

    def draw(self, surf, pos):
        if self.image:
            if self.small:
                true_pos = pos[0] - 4*self.length + 8*self.idx, pos[1] - self.top_pos
            else:
                true_pos = pos[0] - 7*self.length + 14*self.idx, pos[1] - self.top_pos
            surf.blit(self.image, true_pos)

class ScrollArrow():
    images = {'up': SPRITES.get('scroll_arrows'),
              'down': engine.flip_horiz(engine.flip_vert(SPRITES.get('scroll_arrows'))),
              'left': SPRITES.get('page_arrows'),
              'right': engine.flip_horiz(engine.flip_vert(SPRITES.get('page_arrows')))}

    def __init__(self, direction, topleft, offset=0):
        self.x, self.y = topleft
        self.direction = direction
        self.arrow_counter = counters.arrow_counter(offset)
        self.offset = []

    def pulse(self):
        self.arrow_counter.pulse()
        self.offset = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 1, 1]

    def draw(self, surf):
        self.arrow_counter.update()
        if self.direction == 'up':
            pos = (self.x, self.y - (self.offset.pop() if self.offset else 0))
            surf.blit(engine.subsurface(self.images['up'], (0, self.arrow_counter.get() * 8, 14, 8)), pos)
        elif self.direction == 'down':
            pos = (self.x, self.y + (self.offset.pop() if self.offset else 0))
            surf.blit(engine.subsurface(self.images['down'], (0, self.arrow_counter.get() * 8, 14, 8)), pos)
        elif self.direction == 'left':
            pos = (self.x - (self.offset.pop() if self.offset else 0), self.y)
            surf.blit(engine.subsurface(self.images['left'], (self.arrow_counter.get() * 8, 0, 8, 14)), pos)
        elif self.direction == 'right':
            pos = (self.x - (self.offset.pop() if self.offset else 0), self.y)
            surf.blit(engine.subsurface(self.images['right'], (self.arrow_counter.get() * 8, 0, 8, 14)), pos)

class ScrollBar():
    top = engine.subsurface(SPRITES.get('scroll_bar'), (0, 0, 7, 1))
    bottom = engine.subsurface(SPRITES.get('scroll_bar'), (0, 2, 7, 1))
    middle = engine.subsurface(SPRITES.get('scroll_bar'), (0, 1, 7, 1))
    fill = engine.subsurface(SPRITES.get('scroll_bar'), (0, 3, 7, 1))

    def __init__(self):
        self.arrow_counter = counters.arrow_counter()

    def draw(self, surf, topright, scroll, limit, num_options):
        """
        surf -- Surface to draw the scroll bar on
        topright -- Topright coordinate to display scroll bar
        scroll -- How far down the menu has scrolled
        limit -- How many options can be displayed at once
        num_options -- Total number of options in menu
        """
        self.arrow_counter.update()

        # Get properties
        x = topright[0] - 10
        y = topright[1] + 12
        height = limit * 16 - 20
        start_fraction = scroll / num_options
        end_fraction = min(1, (scroll + limit) / num_options)

        # Draw parts
        surf.blit(self.top, (x, y))
        surf.blit(self.bottom, (x, y + height + 2))
        for num in range(1, height + 2):
            surf.blit(self.middle, (x, y + num))

        # Draw bar
        start_pos = int(start_fraction * height)
        end_pos = int(end_fraction * height)
        for num in range(start_pos, end_pos + 1):
            surf.blit(self.fill, (x, y + num + 1))

        # Draw arrows
        if start_pos > 0:
            top_arrow = engine.subsurface(SPRITES.get('scroll_bar'), (8, 4 + self.arrow_counter.get() * 6, 8, 6))
            surf.blit(top_arrow, (x - 1, y - 7))
        if end_pos < height:
            bottom_arrow = engine.subsurface(SPRITES.get('scroll_bar'), (0, 4 + self.arrow_counter.get() * 6, 8, 6))
            surf.blit(bottom_arrow, (x - 1, y + height + 4))
