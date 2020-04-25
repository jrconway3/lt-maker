from app import utilities
from app.data import unit_object
from app.data.database import DB
from app.engine import item_funcs
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
    # print(unit.nid, item1_weapontype, item2_weapontype, advantage)
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
        for sub_component in item.effective.value:
            if sub_component.tag in target.tags:
                might += sub_component.damage
    return might

def attackspeed(unit, item, dist=0):
    if not item:
        item = unit.get_weapon()
    if item and item.custom_attackspeed_equation:
        equation = item.custom_attackspeed_equation
    else:
        equation = 'ATTACKSPEED'
    value = game.equations.get(equation, unit, item, dist)
    # TODO Status
    return value

def accuracy(unit, item=None, dist=0):
    if not item:
        item = unit.get_weapon()
    if not item:
        item = unit.get_spell()
    if not item:
        return None
    if not (item.weapon or item.spell):
        return 10000

    equation = 'HIT'
    if item.custom_hit_equation:
        equation = item.custom_hit_equation

    accuracy = 0
    if item.hit:
        accuracy += item.hit.value + game.equations.get(equation, unit, item, dist)
    else:
        accuracy = 10000
    
    weapon_rank = get_weapon_rank_bonus(unit, item)
    if weapon_rank:
        accuracy += int(weapon_rank.accuracy)
    return accuracy

def avoid(unit, item_to_avoid=None, dist=0):
    if item_to_avoid and item_to_avoid.custom_avoid_equation:
        base = game.equations.get(item_to_avoid.custom_avoid_equation, unit, item_to_avoid, dist)
    else:
        base = game.equations.avoid(unit, item_to_avoid, dist)

    return base

def crit_accuracy(unit, item=None, dist=0):
    if not item:
        item = item.get_weapon()
    if not item:
        item = item.get_spell()
    if not item:
        return None
    if not (item.weapon or item.spell):
        return None

    if item.crit is not None:
        equation = 'CRIT_HIT'
        if item.custom_crit_equation:
            equation = item.custom_crit_equation

        accuracy = item.crit.value + game.equations.get(equation, unit, item, dist)
    
        weapon_rank = get_weapon_rank_bonus(unit, item)
        if weapon_rank:
            accuracy += int(weapon_rank.crit)
    else:
        accuracy = 0
    return accuracy

def crit_avoid(unit, item_to_avoid=None, dist=0):
    if item_to_avoid and item_to_avoid.custom_dodge_equation:
        base = game.equations.get(item_to_avoid.custom_dodge_equation, unit, item_to_avoid, dist)
    else:
        base = game.equations.crit_avoid(unit, item_to_avoid, dist)

    return base

def damage(unit, item=None, dist=0):
    if not item:
        item = item.get_weapon()
    if not item:
        return 0
    if not item.damage:
        return 0

    might = item.damage.value
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
            might += int(weapon_rank.damage)

    return might

def defense(unit, item_to_avoid=None, dist=0):
    if not item_to_avoid:
        res = game.equations.defense(unit, item_to_avoid, dist)
    else:
        if item_to_avoid.custom_defense_equation:
            equation = item_to_avoid.custom_defense_equation
        elif item_funcs.is_magic(item_to_avoid):
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

def compute_heal(unit, target, item, mode=None):
    dist = utilities.calculate_distance(unit.position, target.position)
    if item.heal == 'All':
        heal = game.equations.hitpoints() - target.get_hp()
    elif utilities.is_int(item.heal):
        heal = int(item.heal) + game.equations.heal(unit, item, dist)
    else:
        heal = game.equations.get(item.heal, unit, item, dist)
    # TODO Caretaker 
    return heal

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
        print(adv)
        print(disadv)
        if adv:
            bonus += int(adv.accuracy)
        if disadv:
            bonus += int(disadv.accuracy)

        adv = compute_advantage(unit, target.get_weapon(), item)
        disadv = compute_advantage(unit, target.get_weapon(), item, False)
        if adv:
            bonus -= int(adv.avoid)
        if disadv:
            bonus -= int(disadv.avoid)
        
        hitrate = accuracy(unit, item, dist) + bonus - avoid(target, item, dist)
        return utilities.clamp(hitrate, 0, 100)
    else:
        return 100

def compute_crit(unit, target, item, mode=None):
    if not item: 
        item = unit.get_weapon()
    if not item:
        return None
    if not isinstance(target, unit_object.UnitObject):
        return 0
    if not item.crit:
        return 0
    # TODO cannot be crit
    if (item.weapon or item.spell) and item.crit:
        dist = utilities.calculate_distance(unit.position, target.position)
        bonus = 0

        adv = compute_advantage(unit, item, target.get_weapon())
        disadv = compute_advantage(unit, item, target.get_weapon(), False)
        if adv:
            bonus += int(adv.crit)
        if disadv:
            bonus += int(disadv.crit)

        adv = compute_advantage(unit, target.get_weapon(), item)
        disadv = compute_advantage(unit, target.get_weapon(), item, False)
        if adv:
            bonus -= int(adv.dodge)
        if disadv:
            bonus -= int(disadv.dodge)

        critrate = crit_accuracy(unit, item, dist) + bonus - crit_avoid(target, item, dist)
        return utilities.clamp(critrate, 0, 100)
    else:
        return 0

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
        might += get_effective(item, target)

        # Weapon Triangle
        bonus = 0

        adv = compute_advantage(unit, item, target.get_weapon())
        disadv = compute_advantage(unit, item, target.get_weapon(), False)
        if adv:
            bonus += int(adv.damage)
        if disadv:
            bonus += int(disadv.damage)

        adv = compute_advantage(unit, target.get_weapon(), item)
        disadv = compute_advantage(unit, target.get_weapon(), item, False)
        if adv:
            bonus -= int(adv.resist)
        if disadv:
            bonus -= int(disadv.resist)

        might += bonus
        might -= defense(target, item, dist)

        # Handle crit
        if crit:
            might *= game.equation.crit_mult(unit, item, dist)
            for _ in range(game.equations.crit_add(unit, item, dist)):
                might += damage(unit, item, dist)

        return max(DB.constants.get('min_damage').value, might)

def outspeed(unit, target, item, mode=None) -> bool:
    if not isinstance(target, unit_object.UnitObject):
        return False

    # Weapon Triangle
    bonus = 0

    adv = compute_advantage(unit, item, target.get_weapon())
    disadv = compute_advantage(unit, item, target.get_weapon(), False)
    if adv:
        bonus += int(adv.attackspeed)
    if disadv:
        bonus += int(disadv.attackspeed)

    adv = compute_advantage(unit, target.get_weapon(), item)
    disadv = compute_advantage(unit, target.get_weapon(), item, False)
    if adv:
        bonus -= int(adv.attackspeed)
    if disadv:
        bonus -= int(disadv.attackspeed)

    # Skills and Status TODO
    dist = utilities.calculate_distance(unit.position, target.position)
    val = game.equations.double_atk(unit, item, dist) + bonus - game.equations.double_def(target, item, dist)
    return val > 0
