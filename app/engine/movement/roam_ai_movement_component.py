from __future__ import annotations

from typing import List, Tuple

from app.game_state import game
from app.engine.movement.roam_player_movement_component import RoamPlayerMovementComponent
from app.engine.movement import movement_funcs
from app.utilities import utils

import logging

class RoamAIMovementComponent(RoamPlayerMovementComponent):
    """
    # Used for moving the ai roaming unit according to a path given to it
    """
    def __init__(self, unit):
        super().__init__(follow=False, muted=False)
        self.unit = unit
        # This is the copy we will work with
        self.position = self.unit.position
        self.speed_modifier: float = 1.0
        self.path = []
        self.start()

        self._last_update = 0

    def set_speed(self, mult: float = 1):
        self.speed_modifier = mult

    def set_path(self, path: List[Tuple[float, float]]):
        """
        # How I should get to my goal
        """
        self.path = path

    def get_end_goal(self) -> Tuple[int, int]:
        """
        # Returns what the final goal of this
        # movement is as a position
        """
        return utils.round_pos(self.path[0]) if self.path else self.unit.position

    def get_accel(self):
        return self.base_accel

    def get_desired_vector(self) -> Tuple[float, float]:
        desired_vector = (
            self.path[-1][0] - self.position[0],
            self.path[-1][1] - self.position[1],
        )
        desired_vector = utils.normalize(desired_vector)
        return desired_vector

    def _kinematics(self, delta_time):
        """
        # Updates the velocity of the current unit
        """
        desired_vector = self.get_desired_vector()
        self.x_mag, self.y_mag = desired_vector
        self.x_vel = self.desired_vector[0] * self.speed_modifier
        self.y_vel = self.desired_vector[1] * self.speed_modifier

        # Modify velocity
        self._accelerate(delta_time, self.x_mag, self.y_mag)

    def move(self, delta_time):
        x, y = self.position
        dx = self.x_vel * delta_time
        dy = self.y_vel * delta_time
        next_position = (x + dx, y + dy)

        rounded_pos = utils.rounded_pos(next_position)
        if self._can_move(rounded_pos):
            self.position = next_position

        # Assign the position to the image
        self.unit.sprite.fake_position = self.position

        # Move the unit's true position if necessary
        if rounded_pos != self.unit.position:
            game.leave(self.unit)
            self.unit.position = rounded_pos
            game.arrive(self.unit)
