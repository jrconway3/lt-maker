class Defaults():
    @staticmethod
    def can_select(unit) -> bool:
        return unit.team == 'player'

    @staticmethod
    def check_ally(unit1, unit2) -> bool:
        if unit1 is unit2:
            return True
        elif unit1.team == 'player' or unit1.team == 'other':
            return unit2.team == 'player' or unit2.team == 'other'
        else:
            return unit2.team == unit1.team
        return False

    @staticmethod
    def check_enemy(unit1, unit2) -> bool:
        if unit1.team == 'player' or unit1.team == 'other':
            return not (unit2.team == 'player' or unit2.team == 'other')
        else:
            return not unit2.team == unit1.team
        return True

    @staticmethod
    def can_trade(unit1, unit2) -> bool:
        return unit2.position and unit1.team == unit2.team and check_ally(unit1, unit2)

    @staticmethod
    def exp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def enemy_exp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def sight_range(unit) -> int:
        return 0

    @staticmethod
    def limit_maximum_range(unit, item) -> int:
        return 1000

    @staticmethod
    def modify_maximum_range(unit, item) -> int:
        return 0

    @staticmethod
    def movement_type(unit):
        return None

    @staticmethod
    def modify_buy_price(unit, item) -> float:
        return 1.0

    @staticmethod
    def modify_sell_price(unit, item) -> float:
        return 1.0

# Takes in unit, returns False if not present
default_behaviours = (
    'has_canto', 'pass_through', 'vantage', 'ignore_terrain', 
    'ignore_region_status', 'no_double', 'def_double', 
    'ignore_rescue_penalty', 'ignore_forced_movement', 'distant_counter')
# Takes in unit, returns default value
exclusive_behaviours = ('can_select', 'sight_range', 'movement_type')
# Takes in unit and item, returns default value
item_behaviours = ('modify_buy_price', 'modify_sell_price', 'limit_maximum_range', 'modify_maximum_range')
# Takes in unit and target, returns default value
targeted_behaviours = ('check_ally', 'check_enemy', 'can_trade', 'exp_multiplier', 'enemy_exp_multiplier')
# Takes in unit, item returns bonus
modify_hooks = (
    'modify_damage', 'modify_resist', 'modify_accuracy', 'modify_avoid', 
    'modify_crit_accuracy', 'modify_crit_avoid', 'modify_attack_speed', 
    'modify_defense_speed')
# Takes in unit, item, target, mode, returns bonus
dynamic_hooks = ('dynamic_damage', 'dynamic_resist', 'dynamic_accuracy', 'dynamic_avoid', 
                 'dynamic_crit_accuracy', 'dynamic_crit_avoid', 'dynamic_attack_speed', 'dynamic_defense_speed',
                 'dynamic_multiattacks')
# Takes in unit, item, target, mode returns bonus
multiply_hooks = ('damage_multiplier', 'resist_multiplier')

# Takes in unit
simple_event_hooks = ('on_death',)
# Takes in playback, unit, item, target
combat_event_hooks = ('start_combat', 'end_combat', 'pre_combat', 'post_combat', 'test_on', 'test_off')
# Takes in actions, playback, unit, item, target, mode
subcombat_event_hooks = ('after_hit', 'after_take_hit')
# Takes in unit, item
item_event_hooks = ('on_add_item', 'on_remove_item', 'on_equip_item', 'on_unequip_item')

def condition(skill, unit) -> bool:
    for component in skill.components:
        if component.defines('condition'):
            if not component.condition(unit):
                return False
    return True

for behaviour in default_behaviours:
    func = """def %s(unit):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  return component.%s(unit)
                  return False""" \
        % (behaviour, behaviour, behaviour)
    exec(func)

for behaviour in exclusive_behaviours:
    func = """def %s(unit):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  return component.%s(unit)
                  return Defaults.%s(unit)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

for behaviour in targeted_behaviours:
    func = """def %s(unit1, unit2):
                  for skill in unit1.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit1):
                                  return component.%s(unit1, unit2)
                  return Defaults.%s(unit1, unit2)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

for behaviour in item_behaviours:
    func = """def %s(unit, item):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  return component.%s(unit, item)
                  return Defaults.%s(unit, item)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

for hook in modify_hooks:
    func = """def %s(unit, item):
                  val = 0
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  val += component.%s(unit, item)
                  return val""" \
        % (hook, hook, hook)
    exec(func)

for hook in dynamic_hooks:
    func = """def %s(unit, item, target, mode):
                  val = 0
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  val += component.%s(unit, item, target, mode)
                  return val""" \
        % (hook, hook, hook)
    exec(func)

for hook in multiply_hooks:
    func = """def %s(unit, item, target, mode):
                  val = 1
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  val *= component.%s(unit, item, target, mode)
                  return val""" \
        % (hook, hook, hook)
    exec(func)

for hook in simple_event_hooks:
    func = """def %s(unit):
                  for skill in unit.skills: 
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  component.%s(unit)""" \
        % (hook, hook, hook)
    exec(func)

for hook in combat_event_hooks:
    func = """def %s(playback, unit, item, target):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              if condition(skill, unit):
                                  component.%s(playback, unit, item, target)""" \
        % (hook, hook, hook)
    exec(func)

for hook in subcombat_event_hooks:
    func = """def %s(actions, playback, unit, item, target, mode):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              component.%s(actions, playback, unit, item, target, mode)""" \
        % (hook, hook, hook)
    exec(func)

for hook in item_event_hooks:
    func = """def %s(unit, item):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              component.%s(unit, item)""" \
        % (hook, hook, hook)
    exec(func)

def available(unit, item) -> bool:
    """
    If any hook reports false, then it is false
    """
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('available'):
                if condition(skill, unit):
                    if not component.available(unit, item):
                        return False
    return True

def stat_change(unit, stat) -> int:
    bonus = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('stat_change'):
                if condition(skill, unit):
                    d = component.stat_change(unit)
                    bonus += d.get(stat, 0)
    return bonus

def can_unlock(unit, region) -> bool:
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('can_unlock'):
                if condition(skill, unit):
                    if component.can_unlock(unit, region):
                        return True
    return False

def on_upkeep(actions, playback, unit) -> tuple:  # actions, playback
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('on_upkeep'):
                if condition(skill, unit):
                    component.on_upkeep(actions, playback, unit)
    return actions, playback

def on_endstep(actions, playback, unit) -> tuple:  # actions, playback
    for skill in unit.skills:
        for component in skill.component:
            if component.defines('on_endstep'):
                if condition(skill, unit):
                    component.on_endstep(actions, playback, unit)
    return actions, playback

def on_end_chapter(unit, skill):
    for component in skill.components:
        if component.defines('on_end_chapter'):
            if condition(skill, unit):
                component.on_end_chapter(unit, skill)

def init(skill):
    for component in skill.components:
        if component.defines('init'):
            component.init(skill)

def on_add(unit, skill):
    for component in skill.components:
        if component.defines('on_add'):
            component.on_add(unit, skill)
    for other_skill in unit.skills:
        for component in other_skill.components:
            if component.defines('on_other_skill'):
                component.on_gain_skill(unit, skill)

def on_remove(unit, skill):
    for component in skill.components:
        if component.defines('on_remove'):
            component.on_remove(unit, skill)

def get_text(skill) -> str:
    for component in skill.components:
        if component.defines('text'):
            return component.text()
    return None

def get_cooldown(skill) -> float:
    for component in skill.components:
        if component.defines('cooldown'):
            return component.cooldown()
    return None

def trigger_charge(unit, skill):
    for component in skill.components:
        if component.defines('trigger_charge'):
            component.trigger_charge(unit, skill)
    return None

def get_extra_abilities(unit):
    abilities = {}
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('extra_ability'):
                if condition(skill, unit):
                    new_item = component.extra_ability(unit)
                    ability_name = new_item.name
                    abilities[ability_name] = new_item
    return abilities

def get_combat_arts(unit):
    combat_arts = {}
    for skill in unit.skills:
        combat_art, combat_art_weapons = None, []
        for component in skill.components:
            if component.defines('combat_art'):
                if condition(skill, unit):
                    combat_art = component.combat_art(unit)
            if component.defines('combat_art_weapon_filter'):
                if condition(skill, unit):
                    combat_art_weapons = component.combat_art_weapon_filter(unit)
        if combat_art and combat_art_weapons:
            combat_arts[skill.name] = (skill, combat_art_weapons)
    return combat_arts

def activate_combat_art(unit, skill):
    for component in skill.components:
        if component.defines('on_activation'):
            component.on_activation(unit)

def deactivate_all_combat_arts(unit):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('on_deactivation') and skill.data.get('active'):
                component.on_deactivation(unit)
