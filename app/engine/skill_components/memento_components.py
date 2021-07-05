from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.utilities import utils
from app.engine import equations, action, item_funcs, static_random, skill_system, combat_calcs
from app.engine.game_state import game

class MementoShove(SkillComponent):
    nid = 'memento_shove'
    desc = "All attacks shove target after combat"
    tag = 'memento'

    def _check_shove(self, unit_to_move, anchor_pos, magnitude):
        offset_x = utils.clamp(unit_to_move.position[0] - anchor_pos[0], -1, 1)
        offset_y = utils.clamp(unit_to_move.position[1] - anchor_pos[1], -1, 1)
        new_position = (unit_to_move.position[0] + offset_x,
                        unit_to_move.position[1] + offset_y)

        mcost = game.movement.get_mcost(unit_to_move, new_position)
        if game.tilemap.check_bounds(new_position) and \
                not game.board.get_unit(new_position) and \
                mcost < 99:
            return new_position
        return False

    def cleanup_combat(self, playback, unit, item, target, mode):
        marks = [mark[0] for mark in playback if mark[0] in ('mark_hit', 'mark_crit') and mark[1] is unit and mark[2] is target]
        did_hit = len(marks) > 0
        if did_hit and not skill_system.ignore_forced_movement(target):
            new_position = self._check_shove(target, unit.position, 1)
            if new_position:
                action.do(action.ForcedMovement(target, new_position))
                playback.append(('shove_hit', unit, item, target))
            else:
                # Do half damage again when you shove into a wall
                damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode)
                damage = damage // 2
                action.do(action.ChangeHP(target, -damage))
