from __future__ import annotations

from typing import Dict, List, Tuple
from app.utilities.typing import NID

from app.constants import FRAMERATE
from app.data.database import DB
from app.engine.game_state import game
from app.engine import engine, evaluate, target_system
from app.engine.roam import roam_ai_state
from app.engine.movement.roam_ai_movement_component import RoamAIMovementComponent

class FreeRoamAIHandler:
    def __init__(self):
        self.active: bool = True
        self.roam_ais: List[RoamAI] = []
        # Keep a reference to the movement components
        # we added to the main movement system
        # to be able to stop them later
        self.components: Dict[NID, RoamAIMovementComponent] = {}
        for unit in game.get_all_units():
            if unit.get_roam_ai() and DB.ai.get(unit.get_roam_ai()).roam_ai:
                self.roam_ais.append(RoamAI(unit))
                mc = RoamAIMovementComponent(unit)
                self.components[unit.nid] = mc
                game.movement_system.add(mc)

    def update(self):
        if not self.active:
            return
        for roam_ai in self.roam_ais:
            if roam_ai.state is None:
                roam_ai.think()
            else:
                roam_ai.act()

    def stop(self):
        self.active = False
        for mc in self.components.values():
            mc.finish()

class RoamAI:
    def __init__(self, unit):
        self.unit = unit
        self.reset()
        self.clean_up()

    def reset(self):
        self.state = None
        self.path: List[Tuple[int, int]] = []

        self.behaviour_idx: int = 0
        self.behaviour = None
        self.desired_proximity = 0
        self.speed_mult: float = 1.

    def reset_for_next_behaviour(self):
        self.state = None
        self.path: List[Tuple[int, int]] = []

    def clean_up(self):
        self.goal_item = None
        self.goal_target = None

    def set_next_behaviour(self):
        behaviours = DB.ai.get(self.unit.get_roam_ai()).behaviours
        while self.behaviour_idx < len(behaviours):
            next_behaviour = behaviours[self.behaviour_idx]
            self.behaviour_idx += 1
            if not next_behaviour.condition or \
                    evaluate.evaluate(next_behaviour.condition, self.unit, position=self.unit.position):
                self.behaviour = next_behaviour
                break            
        else:
            self.behaviour_idx = 0
            self.behaviour = None

    def get_path(self, pos) -> List[Tuple[int, int]]:
        return target_system.get_path(self.unit, pos, free_movement=True)

    def think(self):
        start_time = engine.get_time()
        while True:
            # Can spend up to a quarter of a frame thinking
            over_time: bool = engine.get_true_time() - start_time >= FRAMERATE/4
            self.clean_up()

            self.set_next_behaviour()

            if self.behaviour:
                self.desired_proximity = self.behaviour.desired_proximity
                self.speed_mult = self.behaviour.roam_speed

                if self.behaviour.action == 'None':
                    pass  # Try again
                elif self.behaviour.action == "Wait":
                    self.state = roam_ai_state.Wait(self.unit, start_time + self.behaviour.target_spec)
                    return
                elif self.behaviour.action == "Move_to":
                    target = self.get_target()
                    if target:
                        self.state = roam_ai_state.MoveTo(self.unit, target)
                        return
                elif self.behaviour.action == "Interact":
                    self.state = roam_ai_state.Interact(self.unit)
                    return
                elif self.behaviour.action == "Move_away_from":
                    target = self.smart_retreat()
                    if target:
                        self.state = roam_ai_state.MoveTo(self.unit, target)
                        return
            else:  # No behaviour
                return

            if over_time:
                return

    def act(self):
        if self.state.action_type == roam_ai_state.RoamAIAction.MOVE:
            self.move()
        elif self.state.action_type == roam_ai_state.RoamAIAction.WAIT:
            self.wait()
        elif self.state.action_type == roam_ai_state.RoamAIAction.INTERACT:
            self.interact()

    def wait(self):
        if engine.get_time() > self.state.time:
            self.reset_for_next_behaviour()
