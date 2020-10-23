import random, math

from app import counters
from app.utilities import utils
from app.constants import COLORKEY

from app.engine import engine, image_mods

class EventPortrait():
    width, height = 128, 112

    halfblink = (96, 48, 32, 16)
    fullblink = (96, 64, 32, 16)

    openmouth = (0, 96, 32, 16)
    halfmouth = (32, 96, 32, 16)
    closemouth = (64, 96, 32, 16)

    opensmile = (0, 80, 32, 16)
    halfsmile = (32, 80, 32, 16)
    closesmile = (64, 80, 32, 16)

    transition_speed = 233  # 14 frames
    movement_speed = 6  # Each frame move ~6 pixels

    def __init__(self, portrait, position, priority, transition=False, slide=None, mirror=False, expressions=None):
        self.portrait = portrait
        if not self.portrait.image:
            self.portrait.image = engine.image_load(self.portrait.full_path)
            self.portrait.image = self.portrait.image.convert()
            engine.set_colorkey(self.portrait.image, COLORKEY, rleaccel=True)
        self.position = position
        self.priority = priority
        self.transition = transition
        self.transition_update = engine.get_time()
        self.slide = slide
        self.mirror = mirror
        self.expressions = expressions or set()

        self.main_portrait = engine.subsurface(self.portrait.image, (0, 0, 96, 80))

        self.talk_on = False
        self.remove = False

        # For moving
        self.moving = False
        self.orig_position = None
        self.next_position = None
        self.start_movement_time = 0
        self.travel = (0, 0)
        self.travel_mag = 0

        # For talking
        self.talk_state = 0
        self.last_talk_update = 0
        self.next_talk_update = 0

        # For blinking
        # Blinking set up
        self.offset_blinking = [x for x in range(-2000, 2000, 125)]
        # 3 frames for each
        self.blink_counter = counters.generic3counter(7000 + random.choice(self.offset_blinking), 40, 40)

        # For bop
        self.bops_remaining = 0
        self.bop_state = False
        self.last_bop = None

    def bop(self):
        self.bops_remaining = 2
        self.bop_state = False
        self.last_bop = engine.get_time()

    def move(self, position):
        self.orig_position = self.position
        self.next_position = position
        self.moving = True
        self.start_movement_time = engine.get_time()
        self.travel = (self.next_position[0] - self.orig_position[0],
                       self.next_position[1] - self.orig_position[1])
        self.travel_mag = math.sqrt(self.travel[0] ** 2 + self.travel[1]**2)

    def quick_move(self, position):
        self.position = position

    def talk(self):
        self.talk_on = True

    def stop_talking(self):
        self.talk_on = False

    def update_talk(self, current_time):
        # update mouth
        if self.talk_on and current_time - self.last_talk_update > self.next_talk_update:
            self.last_talk_update = self.next_talk_update
            chance = random.randint(1, 10)
            if self.talk_state == 0:
                # 10% chance to skip to state 2    
                if chance == 1:
                    self.talk_state = 2
                    self.next_talk_update = random.randint(70, 160)
                else:
                    self.talk_state = 1
                    self.next_talk_update = random.randint(30, 50)
            elif self.talk_state == 1:
                # 10% chance to go back to state 0
                if chance == 1:
                    self.talk_state = 0
                    self.next_talk_update = random.randint(50, 100)
                else:
                    self.talk_state = 2
                    self.next_talk_update = random.randint(70, 160)
            elif self.talk_state == 2:
                # 10% chance to skip back to state 0
                # 10% chance to go back to state 1
                chance = random.randint(1, 10)
                if chance == 1:
                    self.talk_state = 0
                    self.next_talk_update = random.randint(50, 100)
                elif chance == 2:
                    self.talk_state = 1
                    self.next_talk_update = random.randint(30, 50)
                else:
                    self.talk_state = 3
                    self.next_talk_update = random.randint(30, 50)
            elif self.talk_state == 3:
                self.talk_state = 0
                self.next_talk_update = random.randint(50, 100)
        if not self.talk_on:
            self.talk_state = 0

    def create_image(self):
        main_image = self.main_portrait.copy()
        # For smile image
        if "Smile" in self.expressions:
            if self.talk_state == 0:
                mouth_image = engine.subsurface(self.portrait.image, self.closesmile)
            elif self.talk_state == 1 or self.talk_state == 3:
                mouth_image = engine.subsurface(self.portrait.image, self.halfsmile)
            elif self.talk_state == 2:
                mouth_image = engine.subsurface(self.portrait.image, self.opensmile)
        else:
            if self.talk_state == 0:
                mouth_image = engine.subsurface(self.portrait.image, self.closemouth)
            elif self.talk_state == 1 or self.talk_state == 3:
                mouth_image = engine.subsurface(self.portrait.image, self.halfmouth)
            elif self.talk_state == 2:
                mouth_image = engine.subsurface(self.portrait.image, self.openmouth)
        
        # For blink image
        if "CloseEyes" in self.expressions:
            blink_image = engine.subsurface(self.portrait.image, self.fullblink)
        elif "HalfCloseEyes" in self.expressions:
            blink_image = engine.subsurface(self.portrait.image, self.halfblink)
        elif "OpenEyes" in self.expressions:
            blink_image = None
        else:
            if self.blink_counter.count == 0:
                blink_image = None
            elif self.blink_counter.count == 1:
                blink_image = engine.subsurface(self.portrait.image, self.halfblink)
            elif self.blink_counter.count == 2:
                blink_image = engine.subsurface(self.portrait.image, self.fullblink)
            
        # Piece together image
        if blink_image:
            main_image.blit(blink_image, self.portrait.blinking_offset)
        main_image.blit(mouth_image, self.portrait.smiling_offset)
        return main_image

    def update(self) -> bool:
        current_time = engine.get_time()
        self.update_talk(current_time)
        self.blink_counter.update(current_time)

        if self.transition:
            # 14 frames for unit face to appear
            perc = (current_time - self.transition_update) / self.transition_speed
            if self.remove:
                perc = 1 - perc
            self.transition_progress = perc
            if perc > 1 or perc < 0:
                self.transition = False
                self.transition_progress = utils.clamp(perc, 0, 1)
                if self.remove:
                    return True

        if self.moving:
            diff_pos = (self.next_position[0] - self.position[0],
                        self.next_position[1] - self.position[1])
            if -self.movement_speed <= diff_pos[0] <= self.movement_speed:
                self.position = self.next_position
                self.moving = False
            else:
                perc = (current_time - self.start_movement_time) / (self.travel_mag * self.movement_speed)
                angle = math.atan2(self.travel[1], self.travel[0])
                updated_position = (self.orig_position[0] + self.travel[0] * perc * math.cos(angle), 
                                    self.orig_position[1] + self.travel[1] * perc * math.sin(angle))
                self.position = updated_position                

        if self.bops_remaining:
            if current_time - self.last_bop > 150:
                self.last_bop += 150
                if self.bop_state:
                    self.bops_remaining -= 1
                self.bop_state = not self.bop_state

        return False

    def draw(self, surf):
        image = self.create_image()
        if self.mirror:
            image = engine.flip_horiz(image)

        if self.transition:
            if self.slide:
                image = image_mods.make_translucent(image, 1 - self.transition_progress)
            else:
                image = image_mods.make_black_colorkey(image, 1 - self.transition_progress)

        position = self.position

        if self.slide == 'right':
            position = position[0] - int(24 * self.transition_progress), self.position[1]
        elif self.slide == 'left':
            position = position[0] + int(24 * self.transition_progress), self.position[1]

        if self.bop_state:
            position = position[0], position[1] + 2

        surf.blit(image, position)

    def end(self):
        self.transition = True
        self.remove = True
        self.transition_update = engine.get_time()
