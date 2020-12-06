class Defaults():
    @staticmethod
    def can_select(unit) -> bool:
        return unit.team == 'player'

    @staticmethod
    def check_ally(unit1, unit2) -> bool:
        if unit1.team == 'player' or unit1.team == 'other':
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
    def exp_multiplier(unit1, unit2) -> bool:
        return 1.0

    @staticmethod
    def sight_range(unit) -> int:
        return 0

# Takes in unit, returns False if not present
default_behaviours = ('has_canto', 'pass_through', 'vantage', 'class_skill', 'feat', 'negative', 'ignore_terrain')
# Takes in unit, returns default value
exclusive_behaviours = ('can_select', 'sight_range')
# Takes in unit and target, returns default value
targeted_behaviours = ('check_ally', 'check_enemy', 'can_trade', 'exp_multiplier')
# Takes in unit, item, target, mode, returns bonus
dynamic_hooks = ('dynamic_damage', 'dynamic_resist', 'dynamic_accuracy', 'dynamic_avoid', 
                 'dynamic_crit_accuracy', 'dynamic_crit_avoid', 'dynamic_attack_speed', 'dynamic_defense_speed',
                 'dynamic_multiattacks')
# Takes in unit, item returns bonus
modify_hooks = ('modify_damage', 'modify_resist', 'modify_accuracy', 'modify_avoid', 
                'modify_crit_accuracy', 'modify_crit_avoid', 'modify_attack_speed', 
                'modify_defense_speed')
# Takes in unit, item, target, mode returns bonus
multiply_hooks = ('damage_multiplier', 'resist_multiplier')
# Takes in unit
simple_event_hooks = ('on_end_chapter', )
# Takes in playback, unit, item, target
combat_event_hooks = ('start_combat', 'end_combat')
# Takes in actions, playback, unit, item, target, mode
subcombat_event_hooks = ('on_hit', 'on_crit', 'on_miss', 'on_damage', 'on_take_damage')

for behaviour in default_behaviours:
    func = """def %s(unit):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              return component.%s(unit)
                  return False""" \
        % (behaviour, behaviour, behaviour)
    exec(func)

for behaviour in targeted_behaviours:
    func = """def %s(unit1, unit2):
                  for skill in unit1.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              return component.%s(unit1, unit2)
                  return Defaults.%s(unit1, unit2)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

for behaviour in exclusive_behaviours:
    func = """def %s(unit):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              return component.%s(unit)
                  return Defaults.%s(unit)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

for hook in modify_hooks:
    func = """def %s(unit, item):
                  val = 0
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              val += component.%s(unit, item)
                  return val""" \
        % (hook, hook, hook)
    exec(func)

for hook in dynamic_hooks:
    func = """def %s(unit, item, target, mode):
                  val = 0
                  for skill in unit.skills:
                      for component in item.components:
                          if component.defines('%s'):
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
                              val *= component.%s(unit, item, target, mode)
                  return val""" \
        % (hook, hook, hook)
    exec(func)

for hook in simple_event_hooks:
    func = """def %s(unit):
                  for skill in units.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              component.%s(unit)""" \
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

for hook in combat_event_hooks:
    func = """def %s(playback, unit, item, target):
                  for skill in unit.skills:
                      for component in skill.components:
                          if component.defines('%s'):
                              component.%s(playback, unit, item, target)""" \
        % (hook, hook, hook)
    exec(func)

def can_use_weapon(unit, item) -> bool:
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('can_use_weapon'):
                if not component.can_use_weapon(unit, item):
                    return False
    return True

def stat_change(unit, stat) -> int:
    bonus = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('stat_change'):
                d = component.stat_change(unit)
                bonus += d.get(stat, 0)
    return bonus

def on_upkeep(actions, playback, unit) -> tuple:  # actions, playback
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('on_upkeep'):
                component.on_upkeep(actions, playback, unit)
    return actions, playback

def on_endstep(actions, playback, unit) -> tuple:  # actions, playback
    for skill in unit.skills:
        for component in skill.component:
            if component.defines('on_endstep'):
                component.on_endstep(actions, playback, unit)
    return actions, playback

def init(unit, skill):
    for component in skill.components:
        if component.defines('init'):
            component.init(unit)

def remove(unit, skill):
    for component in skill.components:
        if component.defines('remove'):
            component.remove(unit)

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
