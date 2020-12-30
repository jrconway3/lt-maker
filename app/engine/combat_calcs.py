from app.utilities import utils
from app.data.database import DB
from app.engine import equations, item_system, item_funcs, skill_system

def get_weapon_rank_bonus(unit, item):
    weapon_type = item_system.weapon_type(unit, item)
    if not weapon_type:
        return None
    rank_bonus = DB.weapons.get(weapon_type).rank_bonus
    wexp = unit.wexp[weapon_type]
    for combat_bonus in rank_bonus:
        if combat_bonus.weapon_rank == 'All' or \
                DB.weapon_ranks.get(combat_bonus.weapon_rank).requirement >= wexp:
            return combat_bonus
    return None

def compute_advantage(unit1, unit2, item1, item2, advantage=True):
    if not item1 or not item2:
        return None
    item1_weapontype = item_system.weapon_type(unit1, item1)
    item2_weapontype = item_system.weapon_type(unit2, item2)
    if not item1_weapontype or not item2_weapontype:
        return None
    if advantage:
        bonus = DB.weapons.get(item1_weapontype).advantage
    else:
        bonus = DB.weapons.get(item1_weapontype).disadvantage
    for adv in bonus:
        if adv.weapon_type == 'All' or adv.weapon_type == item2_weapontype:
            if adv.weapon_rank == 'All' or DB.weapon_ranks.get(adv.weapon_rank).requirement >= unit1.wexp[item1_weapontype]:
                return adv
    return None

def can_counterattack(attacker, aweapon, defender, dweapon) -> bool:
    if dweapon and item_funcs.available(defender, dweapon):
        if item_system.can_be_countered(attacker, aweapon) and \
                item_system.can_counter(defender, dweapon):
            if not attacker.position or attacker.position in item_system.valid_targets(defender, dweapon):
                return True
    return False

def accuracy(unit, item=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    accuracy = item_system.hit(unit, item)
    if accuracy is None:
        return None

    equation = item_system.accuracy_formula(unit, item)
    accuracy += equations.parser.get(equation, unit)
    
    weapon_rank_bonus = get_weapon_rank_bonus(unit, item)
    if weapon_rank_bonus:
        accuracy += int(weapon_rank_bonus.accuracy)

    accuracy += item_system.modify_accuracy(unit, item)
    accuracy += skill_system.modify_accuracy(unit, item)

    # TODO
    # Support Bonus

    return accuracy

def avoid(unit, item_to_avoid=None):
    if not item_to_avoid:
        avoid = equations.parser.avoid(unit)
    else:
        equation = item_system.avoid_formula(unit, item_to_avoid)
        avoid = equations.parser.get(equation, unit)
        avoid += item_system.modify_avoid(unit, item_to_avoid)
    avoid += skill_system.modify_avoid(unit, item_to_avoid)
    return avoid

def crit_accuracy(unit, item=None):
    if not item:
        item = item.get_weapon()
    if not item:
        return None

    crit_accuracy = item_system.crit(unit, item)
    if crit_accuracy is None:
        return None

    equation = item_system.crit_accuracy_formula(unit, item)
    crit_accuracy += equations.parser.get(equation, unit)
    
    weapon_rank_bonus = get_weapon_rank_bonus(unit, item)
    if weapon_rank_bonus:
        crit_accuracy += int(weapon_rank_bonus.crit)

    crit_accuracy += item_system.modify_crit_accuracy(unit, item)
    crit_accuracy += skill_system.modify_crit_accuracy(unit, item)

    return crit_accuracy

def crit_avoid(unit, item_to_avoid=None):
    if not item_to_avoid:
        avoid = equations.parser.crit_avoid(unit)
    else:
        equation = item_system.crit_avoid_formula(unit, item_to_avoid)
        avoid = equations.parser.get(equation, unit)
        avoid += item_system.modify_crit_avoid(unit, item_to_avoid)
    avoid += skill_system.modify_crit_avoid(unit, item_to_avoid)
    return avoid

def damage(unit, item=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    might = item_system.damage(unit, item)
    if might is None:
        return None

    equation = item_system.damage_formula(unit, item)
    might += equations.parser.get(equation, unit)

    weapon_rank_bonus = get_weapon_rank_bonus(unit, item)
    if weapon_rank_bonus:
        might += int(weapon_rank_bonus.damage)

    might += item_system.modify_damage(unit, item)
    might += skill_system.modify_damage(unit, item)
    # TODO
    # Support bonus

    return might

def defense(unit, item_to_avoid=None):
    if not item_to_avoid:
        res = equations.parser.defense(unit)
    else:
        equation = item_system.defense_formula(unit, item_to_avoid)
        res = equations.parser.get(equation, unit)
        res += item_system.modify_resist(unit, item_to_avoid)
    res += skill_system.modify_resist(unit, item_to_avoid)
    return res

def attack_speed(unit, item=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    equation = item_system.attack_speed_formula(unit, item)
    attack_speed = equations.parser.get(equation, unit)

    weapon_rank_bonus = get_weapon_rank_bonus(unit, item)
    if weapon_rank_bonus:
        attack_speed += int(weapon_rank_bonus.attack_speed)

    attack_speed += item_system.modify_attack_speed(unit, item)
    attack_speed += skill_system.modify_attack_speed(unit, item)
    # TODO
    # Support bonus

    return attack_speed

def defense_speed(unit, item_to_avoid=None):
    if not item_to_avoid:
        speed = equations.parser.defense_speed(unit)
    else:
        equation = item_system.defense_speed_formula(unit, item_to_avoid)
        speed = equations.parser.get(equation, unit)
        speed += item_system.modify_defense_speed(unit, item_to_avoid)
    speed += skill_system.modify_defense_speed(unit, item_to_avoid)
    return speed

def compute_hit(unit, target, item=None, mode=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    hit = accuracy(unit, item)
    if hit is None:
        return 10000

    # Handles things like effective accuracy
    hit += item_system.dynamic_accuracy(unit, item, target, mode)
    
    # Weapon Triangle
    triangle_bonus = 0
    adv = compute_advantage(unit, target, item, target.get_weapon())
    disadv = compute_advantage(unit, target, item, target.get_weapon(), False)
    if adv:
        triangle_bonus += int(adv.accuracy) * item_system.modify_weapon_triangle(unit, item)
    if disadv:
        triangle_bonus += int(disadv.accuracy) * item_system.modify_weapon_triangle(unit, item)

    adv = compute_advantage(target, unit, target.get_weapon(), item)
    disadv = compute_advantage(target, unit, target.get_weapon(), item, False)
    if adv:
        triangle_bonus -= int(adv.avoid) * item_system.modify_weapon_triangle(target, target.get_weapon())
    if disadv:
        triangle_bonus -= int(disadv.avoid) * item_system.modify_weapon_triangle(target, target.get_weapon())
    hit += triangle_bonus

    hit -= avoid(target, item)

    hit += skill_system.dynamic_accuracy(unit, item, target, mode)
    hit -= skill_system.dynamic_avoid(target, item, unit, mode)

    return utils.clamp(hit, 0, 100)

def compute_crit(unit, target, item=None, mode=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    crit = crit_accuracy(unit, item)
    if crit is None:
        return None

    # Handles things like effective accuracy
    crit += item_system.dynamic_crit_accuracy(unit, item, target, mode)
    
    # Weapon Triangle
    triangle_bonus = 0
    adv = compute_advantage(unit, target, item, target.get_weapon())
    disadv = compute_advantage(unit, target, item, target.get_weapon(), False)
    if adv:
        triangle_bonus += int(adv.crit) * item_system.modify_weapon_triangle(unit, item)
    if disadv:
        triangle_bonus += int(disadv.crit) * item_system.modify_weapon_triangle(unit, item)

    adv = compute_advantage(target, unit, target.get_weapon(), item)
    disadv = compute_advantage(target, unit, target.get_weapon(), item, False)
    if adv:
        triangle_bonus -= int(adv.dodge) * item_system.modify_weapon_triangle(target, target.get_weapon())
    if disadv:
        triangle_bonus -= int(disadv.dodge) * item_system.modify_weapon_triangle(target, target.get_weapon())
    crit += triangle_bonus

    crit -= crit_avoid(target, item)

    crit += skill_system.dynamic_crit_accuracy(unit, item, target, mode)
    crit -= skill_system.dynamic_crit_avoid(target, item, unit, mode)

    return utils.clamp(crit, 0, 100)

def compute_damage(unit, target, item=None, mode=None, crit=False):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    might = damage(unit, item)
    if might is None:
        return None

    # Handles things like effective damage
    might += item_system.dynamic_damage(unit, item, target, mode)

    # Weapon Triangle
    triangle_bonus = 0
    adv = compute_advantage(unit, target, item, target.get_weapon())
    disadv = compute_advantage(unit, target, item, target.get_weapon(), False)
    if adv:
        triangle_bonus += int(adv.damage) * item_system.modify_weapon_triangle(unit, item)
    if disadv:
        triangle_bonus += int(disadv.damage) * item_system.modify_weapon_triangle(unit, item)

    adv = compute_advantage(target, unit, target.get_weapon(), item)
    disadv = compute_advantage(target, unit, target.get_weapon(), item, False)
    if adv:
        triangle_bonus -= int(adv.resist) * item_system.modify_weapon_triangle(target, target.get_weapon())
    if disadv:
        triangle_bonus -= int(disadv.resist) * item_system.modify_weapon_triangle(target, target.get_weapon())
    might += triangle_bonus
    total_might = might

    might -= defense(target, item)

    if crit:
        might *= equations.parser.crit_mult(unit)
        for _ in range(equations.parser.crit_add(unit)):
            might += total_might

    might += skill_system.dynamic_damage(unit, item, target, mode)
    might -= skill_system.dynamic_resist(target, item, unit, mode)

    might *= skill_system.damage_multiplier(unit, item, target, mode)
    might *= skill_system.resist_multiplier(target, item, unit, mode)
    return int(max(DB.constants.get('min_damage').value, might))

def outspeed(unit, target, item, mode=None) -> bool:
    if not item:
        item = unit.get_weapon()
    if not item_system.can_double(unit, item):
        return 1

    speed = attack_speed(unit, item)

    # Handles things like effective damage
    speed += item_system.dynamic_attack_speed(unit, item, target, mode)

    # Weapon Triangle
    triangle_bonus = 0

    adv = compute_advantage(unit, target, item, target.get_weapon())
    disadv = compute_advantage(unit, target, item, target.get_weapon(), False)
    if adv:
        triangle_bonus += int(adv.attack_speed) * item_system.modify_weapon_triangle(unit, item)
    if disadv:
        triangle_bonus += int(disadv.attack_speed) * item_system.modify_weapon_triangle(unit, item)

    adv = compute_advantage(target, unit, target.get_weapon(), item)
    disadv = compute_advantage(target, unit, target.get_weapon(), item, False)
    if adv:
        triangle_bonus -= int(adv.defense_speed) * item_system.modify_weapon_triangle(target, target.get_weapon())
    if disadv:
        triangle_bonus -= int(disadv.defense_speed) * item_system.modify_weapon_triangle(target, target.get_weapon())

    speed -= defense_speed(target, item)

    speed += skill_system.dynamic_attack_speed(unit, item, target, mode)
    speed -= skill_system.dynamic_defense_speed(target, item, unit, mode)

    return 2 if speed >= equations.parser.speed_to_double(unit) else 1

def compute_multiattacks(unit, target, item=None, mode=None):
    if not item:
        item = unit.get_weapon()
    if not item:
        return None

    num_attacks = 1
    num_attacks += item_system.dynamic_multiattacks(unit, item, target, mode)
    num_attacks += skill_system.dynamic_multiattacks(unit, item, target, mode)

    return num_attacks
