from app.data.database import DB

from app.engine import static_random

import logging
logger = logging.getLogger(__name__)

def get_next_level_up(unit) -> dict:
    # TODO Implement support for negative growths
    if unit.team == 'player':
        method = DB.constants.get('player_leveling').value
    else:
        method = DB.constants.get('enemy_leveling').value
        if method == 'Match':
            method = DB.constants.get('player_leveling').value

    r = static_random.get_levelup(unit.nid, unit.get_internal_level * 100)

    stat_changes = {nid: 0 for nid in DB.stats.keys()}
    klass = DB.classes.get(unit.klass)
    for nid in DB.stats.keys():
        growth = unit.growths[nid] + klass.growth_bonus[nid]
        if method == 'Fixed':
            stat_changes[nid] = (unit.growth_points[nid] + growth) // 100
            stat_changes[nid] = min(stat_changes, klass.max_stats[nid] - unit.stats[nid])
            unit.growth_points[nid] = (unit.growth_points[nid] + growth) % 100
        elif method == 'Random':
            while growth > 0:
                if growth >= 100:
                    stat_changes[nid] += 1
                elif r.randint(0, 99) < growth:
                    stat_changes[nid] += 1
                growth -= 100
            stat_changes[nid] = min(stat_changes, klass.max_stats[nid] - unit.stats[nid])
        elif method == 'Dynamic':
            # Growth points used to modify growth 
            variance = 10.  # Lower to reduce variance
            start_growth = growth + unit.growth_points[nid]
            if start_growth <= 0:
                unit.growth_points[nid] += growth/5.
            else:
                free_levels = growth // 100
                stat_changes[nid] += free_levels
                new_growth = growth % 100
                start_growth = new_growth + unit.growth_points[nid]
                if r.randint(0, 99) < int(start_growth):
                    stat_changes[nid] += 1
                    unit.growth_points[nid] -= (100 - new_growth)/variance
                else:
                    unit.growth_points[nid] += new_growth/variance

    return stat_changes

def apply_stat_changes(unit, stat_changes: dict, in_base: bool = True):
    """
    Assumes stat changes are valid!
    """
    logger.info("Applying stat changes %s to %s", stat_changes, unit.nid)
    
    for nid, value in stat_changes.items():
        unit.stats[nid] += value

    if in_base:
        unit.set_hp(1000)
        unit.set_mana(1000)
