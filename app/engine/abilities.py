from app.engine import target_system, skill_system, action, equations
from app.engine.game_state import game

class Ability():
    def targets(self, unit) -> set:
        return set()

    def highlights(self, unit):
        pass

    def do(self, unit):
        pass

class AttackAbility(Ability):
    name = 'Attack'

    def targets(self, unit) -> set:
        if self.cur_unit.has_attacked:
            return set()
        return target_system.get_all_weapon_targets(unit)

    def highlights(self, unit):
        valid_attacks = target_system.get_possible_attacks(unit, {unit.position})
        game.highlight.display_possible_attacks(valid_attacks)

class SpellAbility(Ability):
    name = 'Spell'

    def targets(self, unit) -> set:
        if self.cur_unit.has_attacked:
            return set()
        return target_system.get_all_spell_targets(unit)

    def highlights(self, unit):
        valid_attacks = target_system.get_possible_spell_attacks(unit, {unit.position})
        game.highlight.display_possible_spell_attacks(valid_attacks)

def get_adj_allies(unit) -> list:
    adj_positions = target_system.get_adjacent_positions(unit)
    adj_units = [game.board.get_unit(pos) for pos in adj_positions]
    adj_units = [_ for _ in adj_units if _]
    adj_allies = [u for u in adj_units if skill_system.check_ally(unit, u)]
    return adj_allies

class DropAbility(Ability):
    name = "Drop"

    def targets(self, unit) -> set:
        if unit.traveler and not unit.has_attacked:
            good_pos = set()
            adj_positions = target_system.get_adjacent_positions(unit)
            traveler = unit.traveler
            for adj_pos in adj_positions:
                if not game.board.get_unit(adj_pos) and game.moving_units.get_mcost(unit, adj_pos) <= equations.parser.movement(traveler):
                    good_pos.add(adj_pos)
            return good_pos
        return set()

    def do(self, unit):
        game.state.change('menu')
        u = game.level.units.get(unit.traveler)
        action.do(action.Drop(unit, u, game.cursor.position))

class RescueAbility(Ability):
    name = "Rescue"

    def targets(self, unit) -> set:
        if not unit.traveler and not unit.has_attacked:
            adj_allies = get_adj_allies(unit)
            return set([u.position for u in adj_allies if not u.traveler and
                        equations.parser.rescue_aid(unit) > equations.parser.rescue_weight(u)])

    def do(self, unit):
        u = game.board.get_unit(game.cursor.position)
        action.do(action.Rescue(unit, u))
        if skill_system.has_canto(unit):
            game.state.change('menu')
        else:
            game.state.change('free')
            action.do(action.Wait(unit))
            game.cursor.set_pos(unit.position)

class TakeAbility(Ability):
    name = 'take'

    def targets(self, unit) -> set:
        if not unit.traveler and not unit.has_attacked:
            adj_allies = get_adj_allies(unit)
            return set([u.position for u in adj_allies if u.traveler and
                        equations.parser.rescue_aid(unit) > equations.parser.rescue_weight(game.level.units.get(u.traveler))])

    def do(self, unit):
        u = game.board.get_unit(game.cursor.position)
        action.do(action.Take(unit, u))
        # Taking does not count as major action
        game.state.change('menu')

class GiveAbility(Ability):
    name = 'give'

    def targets(self, unit) -> set:
        if unit.traveler and not unit.has_attacked:
            adj_allies = get_adj_allies(unit)
            return set([u.position for u in adj_allies if not u.traveler and
                        equations.parser.rescue_aid(u) > equations.parser.rescue_weight(game.level.units.get(unit.traveler))])

    def do(self, unit):
        u = game.board.get_unit(game.cursor.position)
        action.do(action.Give(unit, u))
        # Giving does not count as a major action
        game.state.change('menu')

class ItemAbility(Ability):
    name = 'Item'

    def targets(self, unit) -> set:
        if unit.items:
            return {unit.position}
        return set()

class TradeAbility(Ability):
    name = 'Trade'

    def targets(self, unit) -> set:
        adj_allies = get_adj_allies(unit)
        return set([u.position for u in adj_allies if unit.team == u.team])

    def do(self, unit):
        game.state.change('trade')

ABILITIES = Ability.__subclasses__()
