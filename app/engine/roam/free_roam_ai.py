from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from app.utilities.typing import NID

from app.data.database import DB
from app.engine.game_state import game
from app.engine import action, ai_controller, engine, equations, evaluate, target_system, triggers
from app.engine.roam import roam_ai_state
from app.engine.movement.roam_ai_movement_component import RoamAIMovementComponent
from app.engine.objects.region import RegionObject
from app.events.regions import RegionType
from app.utilities import utils

import logging

class FreeRoamAIHandler:
    def __init__(self):
        self.active: bool = True
        self.roam_ais: List[RoamAI] = []
        # Keep a reference to the movement components
        # we added to the main movement system
        # to be able to stop them later
        # And also to set their paths they should be using
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
            if not roam_ai.state:
                roam_ai.think()
            roam_ai.act()
            # Every frame, make sure our movement component has the right path
            if roam_ai.path:
                self.components[roam_ai.unit.nid].set_path(roam_ai.path)

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
        self.path.clear()

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

    def get_target(self) -> Tuple[int, int]:
        return target_system.get_nearest_open_tile(self.unit, self.goal_target)

    def think(self):
        start_time = engine.get_time()
        while True:
            self.clean_up()

            self.set_next_behaviour()

            if self.behaviour:
                self.speed_mult = self.behaviour.roam_speed

                if self.behaviour.action == 'None':
                    pass  # Try again
                elif self.behaviour.action == "Wait":
                    self.state = roam_ai_state.Wait(self.unit, start_time + self.behaviour.target_spec)
                    return
                elif self.behaviour.action == "Move_to":
                    target: Optional[Tuple[int, int]] = self.approach()
                    if target:
                        self.state = roam_ai_state.MoveTo(self.unit, target, self.behaviour.desired_proximity)
                        return
                elif self.behaviour.action == "Interact":
                    region: Optional[RegionObject] = self.find_region()
                    if region:
                        self.state = roam_ai_state.Interact(self.unit, region, self.behaviour.desired_proximity)
                        return
                elif self.behaviour.action == "Move_away_from":
                    target: Optional[Tuple[int, int]] = self.retreat()
                    if target:
                        self.state = roam_ai_state.MoveTo(self.unit, target, self.behaviour.desired_proximity)
                        return
                else:  # Some behaviour that is currently not supported for roaming
                    pass
            else:  # No behaviour
                return

    def get_filtered_target_positions(self) -> List[Tuple[Tuple[int, int], float]]:
        target_positions = ai_controller.get_targets()

        zero_move = max(target_system.find_potential_range(self.unit, True, True), default=0)
        single_move = zero_move + equations.parser.movement(self.unit)
        double_move = single_move + equations.parser.movement(self.unit)

        target_positions = [(pos, utils.calculate_distance(self.unit.position, pos)) for pos in target_positions]

        # Filter away some of the positions
        if self.behaviour.view_range == -4:
            pass
        elif self.behaviour.view_range == -3:
            target_positions = [(pos, mag) for pos, mag in target_positions if mag < double_move]
        elif self.behaviour.view_range == -2:
            target_positions = [(pos, mag) for pos, mag in target_positions if mag < single_move]
        elif self.behaviour.view_range == -1:
            target_positions = [(pos, mag) for pos, mag in target_positions if mag < zero_move]
        else:
            target_positions = [(pos, mag) for pos, mag in target_positions if mag < self.view_range]
        return target_positions

    def approach(self) -> Optional[Tuple[int, int]]:
        target_positions = self.get_filtered_target_positions()
        # Remove mag, keep pos
        target_positions = [t[0] for t in target_positions]
        target_positions = list(sorted(target_positions, key=lambda pos: utils.calculate_distance(self.unit.position, pos)))

        if target_positions:
            target = target_positions[0]
            return target
        else:
            return None

    def retreat(self) -> Optional[Tuple[int, int]]:
        """
        # Returns best position furthest away from the target
        """
        valid_positions = target_system.get_valid_moves(self.unit)
        target_positions = self.get_filtered_target_positions()

        if target_positions:
            target = utils.smart_farthest_away_pos(self.unit.position, valid_positions, target_positions)
            return target
        else:
            return None

    def find_region(self) -> Optional[RegionObject]:
        """
        # Find the closest region to interact with
        """
        regions = []
        pos = self.unit.position
        for r in game.level.regions:
            if r.region_type == RegionType.EVENT and r.sub_nid == self.behaviour.target_spec:
                try:
                    if not r.condition or evaluate.evaluate(r.condition, self.unit, local_args={'region': r}):
                        regions.append(r)
                except:
                    logging.warning("Could not evaluate region conditional %s" % r.condition)
        # Find the closest
        regions = list(sorted(regions, lambda region: min(utils.calculate_distance(pos, rpos) for rpos in region.get_all_positions())))
        if regions:
            region = regions[0]
            return region
        else:
            return None

    def act(self):
        if self.state.action_type == roam_ai_state.RoamAIAction.MOVE:
            self.move(self.state.target)
        elif self.state.action_type == roam_ai_state.RoamAIAction.WAIT:
            self.wait(self.state.time)
        elif self.state.action_type == roam_ai_state.RoamAIAction.INTERACT:
            self.move(self.state.region.center)
            # Then try to interact (will probably fail unless we are close enough)
            self.interact(self.state.region, self.state.desired_proximity)

    def wait(self, target_time):
        if engine.get_time() > target_time:
            self.reset_for_next_behaviour()

    def interact(self, region: RegionObject, proximity: float):
        if any(utils.calculate_distance(self.unit.position, pos) <= proximity for pos in region.get_all_positions()):
            did_trigger = game.events.trigger(triggers.RegionTrigger(region.sub_nid, self.state.unit, pos, region))
            if not did_trigger:  # Just in case we need the generic one
                did_trigger = game.events.trigger(triggers.OnRegionInteract(self.state.unit, pos, region))
            if did_trigger and region.only_once:
                action.do(action.RemoveRegion(region))
            if did_trigger:
                action.do(action.HasAttacked(self.unit))
            self.reset_for_next_behaviour()

    def move(self, target: Tuple[int, int], proximity: float):
        """
        # Called every update while the unit is to be moving
        # Checks if the path should be recalculated
        """
        if not target:
            self.reset_for_next_behaviour()
            return
        if utils.calculate_distance(self.unit.position, target) <= proximity:
            # We've arrived
            self.reset_for_next_behaviour()
            return
        # Check whether the path has diverged too much
        if self.path and self.path[0] != target:
            self.path = self.get_path(target)
        # If we actually just don't have a path
        if not self.path:
            self.path = self.get_path(target)
