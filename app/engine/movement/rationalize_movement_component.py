from __future__ import annotations

from typing import Tuple

from app.engine.movement.movement_component import MovementComponent
from app.utilities import utils

import logging

class RationalizeMovementComponent(MovementComponent):
    """
    # Used for moving all unit's that are off kilter of the 
    # correct unit.position to the correct unit.position
    """
    speed = 6  # In tiles per seconds
    epsilon = 0.01  # In tiles -- when the unit is close enough

    def __init__(self, unit):
        super().__init__(follow=False, muted=True)
        self.unit = unit
        # This is the copy we will work with
        self.position = self.unit.sprite.fake_position
        self.goal = self.unit.position
        self.start()

    def get_position(self) -> Tuple[int, int]:
        return self.unit.position

    def get_end_goal(self):
        return self.goal

    def start(self):
        # What the unit's velocity is
        x_vector = self.unit.position[0] - self.unit.sprite.fake_position[0]
        y_vector = self.unit.position[1] - self.unit.sprite.fake_position[1]
        x_vector, y_vector = utils.normalize((x_vector, y_vector))
        self.x_vel = self.speed * x_vector
        self.y_vel = self.speed * y_vector

    def finish(self, surprise=False):
        self.active = False

    def update(self, current_time: int):
        delta_time_ms = (current_time - self._last_update)
        # Never make delta time too large
        delta_time_ms = min(delta_time_ms, utils.frames2ms(4))
        delta_time = delta_time_ms / 1000  # Get delta time in seconds
        self._last_update = current_time

        if not self.active:
            return

        if not self.unit.position:
            logging.error("Unit %s is no longer on the map", self.unit)
            self.active = False
            return

        x, y = self.position
        dx = self.x_vel * delta_time
        dy = self.y_vel * delta_time
        next_x = x + dx
        if dx > 0 and x + dx > self.goal[0]:
            next_x = min(x + dx, self.goal[0])
        elif dx < 0 and x + dx < self.goal[0]:
            next_x = max(x + dx, self.goal[0])
        next_y = y + dy
        if dy > 0 and y + dy > self.goal[1]:
            next_y = min(y + dy, self.goal[1])
        elif dy < 0 and y + dy < self.goal[1]:
            next_y = max(y + dy, self.goal[1])
        self.position = (next_x, next_y)

        # Assign the position to the image
        self.unit.sprite.fake_position = self.position

        # If we are really close to our goal position
        # Just finish up
        if (abs(self.position[0] - self.goal[0]) < self.epsilon) or \
                (abs(self.position[1] - self.goal[1]) < self.epsilon):
            self.unit.sprite.fake_position = None
            self.finish()
