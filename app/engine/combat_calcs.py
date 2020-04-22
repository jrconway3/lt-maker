from app import utilities
from app.data import unit_object
from app.data.database import DB
from app.engine.game_state import game

def get_weapon_rank_bonus(unit, item):
    if item.weapon:
        weapon_type = item.weapon.value
    elif item.spell:
        weapon_type = item.spell.weapon_type
    else:
        return None

    highest_rank = None
    for weapon_rank in DB.weapon_ranks:
        if unit.wexp[weapon_type] >= weapon_rank.requirement:
            highest_rank = weapon_rank
    return highest_rank

def compute_advantage(item1, item2)

def accuracy(unit, item=None, dist=0):
    if not item:
        item = unit.get_weapon()
    if not item:
        item = unit.get_spell()
    if not item:
        return None
    equation = 'HIT'
    if item.custom_hit_equation:
        equation = item.custom_hit_equation

    accuracy = 0
    if (item.weapon or item.spell) and item.hit:
        accuracy += item.hit + game.equations.get(equation, unit, item, dist)
    else:
        accuracy = 10000

    if item.weapon or item.spell:
        weapon_rank = get_weapon_rank_bonus(unit, item)
        if weapon_rank:
            accuracy += weapon_rank.accuracy
    return accuracy

def avoid(unit, item_to_avoid=None, dist=0):
    if item_to_avoid and item_to_avoid.custom_avoid_equation:
        base = game.equations.get(item_to_avoid.custom_avoid_equation, unit, item_to_avoid, dist)
    else:
        base = game.equations.avoid(unit, item_to_avoid, dist)

    return base

def damage(unit, item=None, dist=0):
    if not item:
        item = item.get_weapon()
    if not item:
        return 0
    if not item.damage:
        return 0

    might = item.damage
    if item.custom_damage_equation:
        equation = item.custom_damage_equation
    elif item.is_magic():
        equation = 'MAGIC_DAMAGE'
    else:
        equation = 'DAMAGE'
    might += game.equations.get(equation, unit, item, dist)

    if item.weapon or item.spell:
        weapon_rank = get_weapon_rank_bonus(unit, item)
        if weapon_rank:
            might += weapon_rank.damage

    return might

def defense(unit, item_to_avoid=None, dist=0):
    if not item_to_avoid:
        res = game.equations.defense(unit, item_to_avoid, dist)
    else:
        if item_to_avoid.custom_defense_equation:
            equation = item_to_avoid.custom_defense_equation
        elif item_to_avoid.is_magic():
            equation = 'MAGIC_DEFENSE'
        else:
            equation = 'DEFENSE'

        if item_to_avoid.ignore_defense:
            res = 0
        elif item_to_avoid.ignore_half_defense:
            res = game.equations.get(equation, unit, item_to_avoid, dist)//2
        else:
            res = game.equations.get(equation, unit, item_to_avoid, dist)

    return res

def compute_hit(unit, target, item=None, mode=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None
    if not isinstance(target, unit_object.UnitObject):
        return 100

    # Calculations
    if item.weapon or item.spell:
        dist = utilities.calculate_distance(unit.position, target.position)
        advantage = compute_advantage(item, target.get_weapon())
        bonus = 0
        if advantage[0] > 0:
            bonus += advantage[0] * get_advantage(unit, item).accuracy
        else:
            bonus -= advantage[0] * get_disadvantage(unit, item).accuracy
        if advantage[1] > 0:
            bonus -= advantage[1] * get_advantage(target, target.get_weapon()).avoid
        else:
            bonus += advantage[1] * get_disadvantage(target, target.get_weapon()).avoid

        hitrate = accuracy(unit, item, dist) + bonus - avoid(target, item, dist)
        return utilities.clamp(hitrate, 0, 100)
    else:
        return 100

def compute_damage(unit, target, item=None, mode=None, crit=False):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None
    if not (item.weapon or item.spell):
        return 0
    if not item.might:
        return 0

    dist = utilities.calculate_distance(unit.position, target.position)
    might = damage(unit, item, dist)

    if not isinstance(target, unit_object.UnitObject):
        pass
    else:
        # Determine effective
        if item.effective:
            for sub_component in item.effective:
                if sub_component.tag in target.tags:
                    might += sub_component.damage
        # Weapon Triangle
        advantage = compute_advantage(item, target.get_weapon())
        bonus = 0
        if advantage[0] > 0:
            bonus += advantage[0] * get_advantage(unit, item).damage
        else:
            bonus -= advantage[0] * get_disadvantage(unit, item).damage
        if advantage[1] > 0:
            bonus -= advantage[1] * get_advantage(target, target.get_weapon()).resist
        else:
            bonus += advantage[1] * get_disadvantage(target, target.get_weapon()).resist

        might -= defense(target, item, dist)

        # Handle crit
        if crit:
            might *= game.equation.crit_mult(unit, item, dist)
            for _ in range(game.equations.crit_add(unit, item, dist)):
                might += damage(unit, item, dist)

        return max(DB.constants.get('min_damage'), might)







