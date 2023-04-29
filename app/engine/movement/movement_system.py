from __future__ import annotations

from typing import List, Tuple

import app.engine.config as cf
from app.game_state import game
from app.engine import engine
from app.engine.movement.movement_component import MovementComponent
from app.engine.movement.unit_path_movement_component import UnitPathMovementComponent

import logging

# TODO()
# Unit Sprite has some old functions that use MovementSystem
# Make sure roaming state cannot go out of bounds
# Reimplement remaining funcs (get_next_location, can_move, no_bumps) from roam_state
# Roam AI movement
# Replace rationalize everywhere with utils.round_pos()

class MovementSystem:
    """
    Operates upon MovementComponents and handles moving the camera around
    """
    def __init__(self):
        self.moving_entities: List[MovementComponent] = []
        self.camera_follow: Tuple[int, int] = None  # What position to be over
        self.camera_center: bool = False  # Whether to center on the position

    def __len__(self):
        return len(self.moving_entities)

    def add(self, mc: MovementComponent):
        self.moving_entities.append(mc)

    def check_if_occupied_in_future(self, pos):
        for movement_component in self.moving_entities:
            if movement_component.get_end_goal() == pos:
                return movement_component.unit
        return None

    def begin_move(self, unit, path: List[Tuple[int, int]], 
                   event=False, follow=True, speed=0):
        """
        # Used for simple movement of a unit in the normal way
        """

        logging.info("Unit %s to begin moving")
        speed = speed or cf.SETTINGS['unit_speed']
        movement_component = \
            UnitPathMovementComponent(unit, path, event, follow, speed=speed)
        self.moving_entities.append(movement_component)

    def update(self):
        current_time = engine.get_time()
        old_follow = self.camera_follow

        # Update all remaining entities
        for entity in self.moving_entities[:]:
            entity.update(current_time)
            if not self.camera_follow and entity.follow:
                self.camera_follow = entity.get_position()
                self.camera_center = entity.should_camera_center()
            # Remove inactive entities
            if not entity.active:
                self.moving_entities.remove(entity)

        # Update camera follow only if it's changed
        if self.camera_follow and old_follow != self.camera_follow:
            game.cursor.set_pos(self.camera_follow)
            if self.camera_center:
                game.camera.set_center(*self.camera_follow)
