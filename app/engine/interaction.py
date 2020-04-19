from app.data.item_components import SpellAffect, AOEMode
from app import utilities
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

def get_aoe(item, user, atk_pos, target_pos) -> tuple:
    if not item.aoe:
        return target_pos, set()
    if item.aoe.value == AOEMode.Cleave:
        x, y = atk_pos
        other_pos = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                     (x - 1, y), (x + 1, y),
                     (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)]
        splash_positions = {pos for pos in other_pos if game.tilemap.check_bounds(pos) and 
                            not utilities.compare_teams(user.team, game.grid.get_team(pos))}
        return target_pos, splash_positions - {target_pos}
    elif item.aoe.value == AOEMode.AllAllies:
        splash_positions = {unit.position for unit in game.level.units if unit.position and game.target.check_ally(user, unit)}
        return None, splash_positions
    elif item.aoe.value == AOEMode.AllEnemies:
        splash_positions = {unit.position for unit in game.level.units if unit.position and game.target.check_enemy(user, unit)}
        return None, splash_positions
    elif item.aoe.value == AOEMode.AllUnits:
        splash_positions = {unit.position for unit in game.level.units if unit.position}
        return None, splash_positions

def convert_positions(attacker, atk_position, target_position, item):
    logger.info("Attacker Position: %s, Target Position: %s, Item: %s", atk_position, target_position, item)
    if item.weapon or item.spell:
        def_position, splash_positions = get_aoe(item, attacker, atk_position, target_position)
    else:
        def_position, splash_positions = target_position, set()
    logger.info('Defender Position: %s, Splash Pos: %s', def_position, splash_positions)

    if def_position:
        main_defender = game.grid.get_unit(def_position)
        # Also tiles here
    else:
        main_defender = None
    splash_units = [unit for unit in game.level.units if unit.position in splash_positions]

    # Beneficial Stuff only helps allies
    if item.spell and item.spell.affect == SpellAffect.Helpful:
        splash_units = [unit for unit in splash_units if game.targets.check_ally(attacker, unit)]
        if item.heal:  # Only heal allies who need it
            splash_units = [unit for unit in splash_units if unit.get_hp() < game.equations.hitpoints(unit)]
    # if item.weapon or (item.spell and item.spell.affect != SpellAffect.Helpful):
    #     splash_units += Tiles!
    logger.info("Main Defender: %s, Splash: %s" % main_defender, splash_units)
    return main_defender, splash_units

