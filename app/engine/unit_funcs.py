from app.data.database import DB

from app.engine import static_random, item_funcs

import logging
logger = logging.getLogger(__name__)

def get_next_level_up(unit) -> dict:
    # TODO Implement support for negative growths
    if unit.team == 'player':
        method = DB.constants.value('player_leveling')
    else:
        method = DB.constants.value('enemy_leveling')
        if method == 'Match':
            method = DB.constants.value('player_leveling')

    r = static_random.get_levelup(unit.nid, unit.get_internal_level())

    stat_changes = {nid: 0 for nid in DB.stats.keys()}
    klass = DB.classes.get(unit.klass)
    for nid in DB.stats.keys():
        growth = unit.growths[nid] + klass.growth_bonus.get(nid).value
        if method == 'Fixed':
            stat_changes[nid] = (unit.growth_points[nid] + growth) // 100
            stat_changes[nid] = min(stat_changes, klass.max_stats.get(nid).value - unit.stats[nid])
            unit.growth_points[nid] = (unit.growth_points[nid] + growth) % 100
        elif method == 'Random':
            while growth > 0:
                if growth >= 100:
                    stat_changes[nid] += 1
                elif r.randint(0, 99) < growth:
                    stat_changes[nid] += 1
                growth -= 100
            stat_changes[nid] = min(stat_changes[nid], klass.max_stats.get(nid).value - unit.stats[nid])
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

def get_starting_skills(unit) -> list:
    # Class skills
    klass_obj = DB.classes.get(unit.klass)
    current_klass = klass_obj
    all_klasses = [klass_obj]
    while current_klass and current_klass.tier > 1:
        if klass_obj.promotes_from:
            current_klass = DB.classes.get(klass_obj.promotes_from)
            all_klasses.append(current_klass)
        else:
            break
    all_klasses.reverse()
    
    skills_to_add = []
    for idx, klass in enumerate(all_klasses):
        for learned_skill in klass.learned_skills:
            if learned_skill.level <= unit.level or klass != klass_obj:
                skills_to_add.append(learned_skill.skill_nid)

    klass_skills = item_funcs.create_skills(unit, skills_to_add)
    return klass_skills

def get_personal_skills(unit, prefab):
    skills_to_add = []
    for learned_skill in prefab.learned_skills:
        if learned_skill.level <= unit.level:
            skills_to_add.append(learned_skill.skill_nid)

    personal_skills = item_funcs.create_skills(unit, skills_to_add)
    return personal_skills
