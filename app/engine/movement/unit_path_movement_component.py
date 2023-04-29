from __future__ import annotations

from typing import List, Tuple

from app.game_state import game
from app.engine import action
from app.engine.movement.movement_component import MovementComponent
from app.engine.movement import movement_funcs
from app.engine.sound import get_sound_thread

import logging

class UnitPathMovementComponent(MovementComponent):
    """
    # Used for moving a unit along a path
    """
    def __init__(self, unit, path: List[Tuple[int, int]], event=False, 
                 follow=True, muted=False, speed: int = 0):
        super().__init__(follow, muted)
        self.unit = unit
        self.path = path
        self.goal = self.path[0] if self.path else None
        self.event: bool = event
        # How fast we move to each new position in the path
        self.speed = int(speed)
        self.start()

        self._last_update = 0

    def get_position(self):
        return self.unit.position

    def get_end_goal(self):
        return self.goal

    def start(self):
        self.unit.sprite.set_speed(self.speed)
        self.unit.sprite.change_state('moving')
        game.leave(self.unit)
        if not self.muted:
            self.unit.sound.play()

    def update(self, current_time: int):
        if self.active and current_time - self._last_update > self.speed:
            self._last_update = current_time

            if not self.unit.position:
                logging.error("Unit %s is no longer on the map", self.unit)
                self.active = False
                return

            if self.path:
                self._handle_path()
            else:  # Path is empty, we are done
                surprise = movement_funcs.check_region_interrupt(self.unit.position)
                self.finish(surprise=surprise)

    def _handle_path(self):
        next_position = self.path.pop()
        if self.unit.position != next_position:
            if movement_funcs.check_position(
                    self.unit, next_position, 
                    self.goal == next_position, self.event):
                logging.debug("%s moved to %s", self.unit, next_position)
                mcost = movement_funcs.get_mcost(self.unit, next_position)
                self.unit.consume_movement(mcost)
            else:  # This new position ain't valid
                logging.debug("%s can't move any further", self.unit)
                self.finish(surprise=True)
                return

        self.unit.position = next_position

    def finish(self, surprise=False):
        """
        # Called when the unit has finished their movement
        # surprise will be True when the unit has run into an obstacle
        # (enemy unit, interrupt region, etc) that was not expected to
        # be there, and therefore their movement was interrupted

        """
        if surprise:
            get_sound_thread().play_sfx('Surprise')
            self.unit.sprite.change_state('normal')
            self.unit.sprite.reset()
            action.do(action.HasAttacked(self.unit))
            if self.unit.team == 'player':
                game.state.clear()
                game.state.change('free')
                game.state.change('wait')
                # Dummy state change so that game.state.back() at the end of the movement state
                # will just get rid of this instead
                game.state.change('wait')
            if game.ai.unit is self.unit:
                game.ai.interrupt()

        game.arrive(self.unit)
        if self.unit.sound:
            self.unit.sound.stop()

        if self.event:
            self.unit.sprite.change_state('normal')
            action.do(action.Reset(self.unit))
            action.do(action.UpdateFogOfWar(self.unit))
        else:
            self.unit.has_moved = True

        self.active = False
