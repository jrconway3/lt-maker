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

def compute_advantage(unit, item1, item2, advantage=True):
    if not item1 or not item2:
        return None
    item1_weapontype = item1.weapon.value if item1.weapon else item1.spell.weapon_type if item1.spell else None
    item2_weapontype = item2.weapon.value if item2.weapon else item2.spell.weapon_type if item2.spell else None
    if not item1_weapontype or not item2_weapontype:
        return None
    if advantage:
        bonus = DB.weapons.get(item1_weapontype).advantage
    else:
        bonus = DB.weapons.get(item1_weapontype).disadvantage
    for adv in bonus:
        if adv.weapon_type == 'All' or adv.weapon_type == item2_weapontype:
            if adv.weapon_rank == 'All' or DB.weapon_ranks.get(adv.weapon_rank).requirement >= unit.wexp[item1_weapontype]:
                return adv
    return None

def get_effective(item, target):
    might = 0
    if item.effective:
        for sub_component in item.effective:
            if sub_component.tag in target.tags:
                might += sub_component.damage
    return might

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
        bonus = 0

        adv = compute_advantage(unit, item, target.get_weapon())
        disadv = compute_advantage(unit, item, target.get_weapon(), False)
        if adv:
            bonus += adv.accuracy
        if disadv:
            bonus += disadv.accuracy

        adv = compute_advantage(unit, target.get_weapon(), item)
        disadv = compute_advantage(unit, target.get_weapon(), item, False)
        if adv:
            bonus -= adv.avoid
        if disadv:
            bonus -= disadv.avoid
        
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
        might = get_effective(item, target)

        # Weapon Triangle
        bonus = 0

        adv = compute_advantage(unit, item, target.get_weapon())
        disadv = compute_advantage(unit, item, target.get_weapon(), False)
        if adv:
            bonus += adv.damage
        if disadv:
            bonus += disadv.damage

        adv = compute_advantage(unit, target.get_weapon(), item)
        disadv = compute_advantage(unit, target.get_weapon(), item, False)
        if adv:
            bonus -= adv.resist
        if disadv:
            bonus -= disadv.resist

        might += bonus
        might -= defense(target, item, dist)

        # Handle crit
        if crit:
            might *= game.equation.crit_mult(unit, item, dist)
            for _ in range(game.equations.crit_add(unit, item, dist)):
                might += damage(unit, item, dist)

        return max(DB.constants.get('min_damage'), might)
