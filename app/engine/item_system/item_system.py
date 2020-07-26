import random

# Only for exclusive behaviours
class Defaults():
    @staticmethod
    def minimum_range(unit, item) -> int:
        return 0

    @staticmethod
    def maximum_range(unit, item) -> int:
        return 0

    @staticmethod
    def splash(unit, item, position) -> tuple:
        """
        Returns main target and splash
        """
        from app.engine.game_state import game
        return game.grid.get_unit(position), []

    @staticmethod
    def damage(unit, item) -> int:
        return None

    @staticmethod
    def splash_multiplier(unit, item) -> int:
        return 1

    @staticmethod
    def damage_formula(unit, item) -> str:
        return 'DAMAGE'

default_behaviours = ('is_weapon', 'is_spell', 'equippable', 'can_use', 'locked', 'can_counter', 'can_be_countered')
# These behaviours default to false

for behaviour in default_behaviours:
    func = """def %s(unit, item):
                  for component in item.components:
                      if component.defines('%s'):
                          return component.%s(unit, item)
                  return False""" \
        % (behaviour, behaviour, behaviour)
    exec(func)

exclusive_behaviours = ('minimum_range', 'maximum_range', 'splash', 'damage', 'splash_multiplier', 'damage_formula')

for behaviour in exclusive_behaviours:
    func = """def %s(unit, item):
                  for component in item.components:
                      if component.defines('%s'):
                          return component.%s(unit, item)
                  return Defaults.%s(unit, item)""" \
        % (behaviour, behaviour, behaviour, behaviour)
    exec(func)

event_behaviours = ('on_use', 'on_not_available', 'on_end_chapter')

for behaviour in event_behaviours:
    func = """def %s(unit, item):
                  for component in item.components:
                      if component.defines('%s'):
                          component.%s(unit, item)""" \
        % (behaviour, behaviour, behaviour)
    exec(func)

def get_range(unit, item) -> set:
    min_range, max_range = 0, 0
    for component in item.components:
        if component.defines('minimum_range'):
            min_range = component.minimum_range(unit, item)
            break
    for component in item.components:
        if component.defines('maximum_range'):
            max_range = component.maximum_range(unit, item)
            break
    return set(range(min_range, max_range + 1))

def valid_targets(unit, item) -> set:
    targets = set()
    for component in item.components:
        if component.defines('valid_targets'):
            targets |= component.valid_targets(unit, item)
    return targets

def available(unit, item) -> bool:
    for component in item.components:
        if component.defines('available'):
            if not component.available(unit, item):
                return False
    return True

def find_hp(actions, target):
    starting_hp = target.get_hp()
    for action in actions:
        if isinstance(action, action.ChangeHP):
            starting_hp += action.num
    return starting_hp

def on_hit(actions, playback, unit, item, target, mode=None):
    for component in item.components:
        if component.defines('on_hit'):
            component.on_hit(actions, playback, unit, item, target, mode)

    # Default playback
    if find_hp(actions, target) <= 0:
        playback.append(('shake', 2))
        if not any(action for action in playback if action[0] == 'hit_sound'):
            playback.append(('hit_sound', 'Final Hit'))
    else:
        playback.append(('shake', 1))
        if not any(action[0] == 'hit_sound' for action in playback):
            playback.append(('hit_sound', 'Attack Hit ' + str(random.randint(1, 5))))
    playback.append(('unit_tint', target, (255, 255, 255)))

def on_crit(actions, playback, unit, item, target, mode=None):
    for component in item.components:
        if component.defines('on_crit'):
            component.on_crit(actions, playback, unit, item, target, mode)
        elif component.defines('on_hit'):
            component.on_hit(actions, playback, unit, item, target, mode)

    # Default playback
    playback.append(('shake', 3))
    if not any(action for action in playback if action[0] == 'hit_sound'):
        if find_hp(actions, target) <= 0:
            playback.append(('hit_sound', 'Final Hit'))
        else:
            playback.append(('hit_sound', 'Critical Hit ' + str(random.randint(1, 2))))
    playback.append(('unit_tint', target, (255, 255, 255)))

def on_miss(actions, playback, unit, item, target, mode=None):
    for component in item.components:
        if component.defines('on_miss'):
            component.on_miss(actions, playback, unit, item, target, mode)

    # Default playback
    playback.append(('hit_sound', 'Attack Miss 2'))
    playback.append(('hit_anim', 'MapMiss', target))
