from enum import IntEnum

from app.data.data import Data, Prefab

# Custom Types
class SpellAffect(IntEnum):
    Helpful = 1
    Neutral = 2
    Harmful = 3

class SpellTarget(IntEnum):
    Ally = 1
    Enemy = 2
    Unit = 3
    Tile = 4
    TileWithoutUnit = 5

class AOEMode(IntEnum):
    Normal = 1
    All = 2
    CrossCleave = 3
    SquareCleave = 4
    FatCross = 5
    FatCrossWithHole = 6
    Square = 7
    SquareWithHole = 8
    Line = 9
    ThickLine = 10

class ForcedMovement(IntEnum):
    Shove = 1
    Swap = 2
    Warp = 3

# Requirement functions
def no_requirement(other_components):
    return True

def requires_weapon(other_components):
    return 'weapon' in other_components

def requires_spell(other_components):
    return 'spell' in other_components

def requires_spell_or_weapon(other_components):
    return 'weapon' in other_components or 'spell' in other_components

def requires_usable(other_components):
    return 'usable' in other_components

def requires_aspect(other_components):
    return 'weapon' in other_components or 'spell' in other_components or 'usable' in other_components

def requires_might(other_components):
    return 'might' in other_components

def requires_hit(other_components):
    return 'hit' in other_components

def requires_might_and_hit(other_components):
    return 'might' in other_components and 'hit' in other_components

def requires_crit(other_components):
    return 'crit' in other_components

def requires_uses(other_components):
    return 'uses' in other_components or 'c_uses' in other_components

def repair_requires(other_components):
    must_not_have = set('might', 'hit', 'crit', 'hit_status', 'heal_on_hit', 'aoe', 'multiple_targets')
    return ('spell' in other_components and not other_components & must_not_have)

def requires_multiple_targets(other_components):
    return 'multiple_targets' in other_components

class BasicSubComponent(Prefab):
    def __init__(self, nid):
        self.nid: str = nid

    def serialize(self):
        return self.nid

    @classmethod
    def deserialize(cls, s):
        self = cls(s)
        return self

class EffectiveSubComponent(Prefab):
    def __init__(self, tag, damage):
        self.tag: str = tag
        self.damage: int = damage

    @property
    def nid(self):
        return self.tag

    @nid.setter
    def nid(self, value):
        self.tag = value

    def serialize(self):
        return (self.tag, self.damage)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(s_tuple[0], s_tuple[1])
        return self

class StatChangeSubComponent(EffectiveSubComponent):
    def __init__(self, stat, amount):
        self.stat: str = stat
        self.amount: int = amount

    @property
    def nid(self):
        return self.stat

    @nid.setter
    def nid(self, value):
        self.stat = value

    def serialize(self):
        return (self.stat, self.amount)

class GrowthChangeSubComponent(StatChangeSubComponent):
    def __init__(self, stat, percent):
        self.stat: str = stat
        self.percent: int = percent

    def serialize(self):
        return (self.stat, self.percent)

class TargetSubComponent(Prefab):
    def __init__(self, nid, min_range, max_range, target):
        self.nid: str = nid
        self.min_range: str = min_range
        self.max_range: str = max_range
        self.target: SpellTarget = target

    def serialize(self):
        return (self.nid, self.min_range, self.max_range, self.target)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(*s_tuple)
        return self

class EffectiveData(Data):
    datatype = EffectiveSubComponent
    
    def add_new_default(self, DB):
        for tag in DB.tags:
            if tag.nid not in self.keys():
                nid = tag.nid
                break
        else:
            nid = DB.tags[0].nid
        self.append(EffectiveSubComponent(nid, 0))

class StatChangeData(Data):
    datatype = StatChangeSubComponent

    def add_new_default(self, DB):
        for stat in DB.stats:
            if stat.nid not in self.keys():
                nid = stat.nid
                break
        else:
            stat = DB.stats[0].nid
        self.append(self.datatype(nid, 0))

class GrowthChangeData(Data):
    datatype = GrowthChangeSubComponent

class PrfUnitData(Data):
    datatype = BasicSubComponent

    def add_new_default(self, DB):
        for unit in DB.units:
            if unit.nid not in self.keys():
                nid = unit.nid
                break
        else:
            nid = DB.units[0].nid
        self.append(BasicSubComponent(nid))

class PrfClassData(Data):
    datatype = BasicSubComponent

    def add_new_default(self, DB):
        for klass in DB.classes:
            if klass.nid not in self.keys():
                nid = klass.nid
                break
        else:
            nid = DB.classes[0].nid
        self.append(self.datatype(nid))

class PrfTagData(Data):
    datatype = BasicSubComponent

    def add_new_default(self, DB):
        for tag in DB.tags:
            if tag.nid not in self.keys():
                nid = tag.nid
                break
        else:
            nid = DB.tags[0].nid
        self.append(self.datatype(nid))

class PromoteData(PrfClassData):
    pass

class ClassChangeData(PrfClassData):
    pass

class TargetData(Data):
    datatype = TargetSubComponent
    
    def add_new_default(self, DB):
        self.append(TargetSubComponent(len(self), 1, 1, SpellTarget.Enemy))

class ItemComponent():
    def __init__(self, nid=None, name='', attr=bool, value=True, requires=no_requirement, volatile=False):
        self.nid: str = nid
        self.name: str = name
        self.attr = attr
        self.value = value
        self.requires = requires
        self.volatile: bool = volatile

    def __getstate__(self):
        return self.nid, self.value

    def __setstate__(self, state):
        self.nid, self.value = state

    @classmethod
    def copy(cls, other):
        return cls(other.nid, other.name, other.attr, other.value, other.requires)

    def serialize(self):
        if isinstance(self.value, Data):
            return self.nid, self.value.save()
        elif isinstance(self.value, list):
            return self.nid, self.value
        else:
            return (self.nid, self.value)

    # For spell component only
    @property
    def weapon_type(self):
        return self.value[0]

    @property
    def affect(self):
        return self.value[1]

    @property
    def target(self):
        return self.value[2]

item_components = Data([
    ItemComponent('weapon', 'Weapon', 'WeaponType', None,
                  lambda x: 'spell' not in x),
    ItemComponent('spell', 'Spell', ('WeaponType', SpellAffect, SpellTarget),
                  (None, SpellAffect.Neutral, SpellTarget.Unit),
                  lambda x: 'weapon' not in x),
    ItemComponent('usable', 'Usable'),
    ItemComponent('might', 'Might', int, 0, requires_spell_or_weapon),
    ItemComponent('hit', 'Hit Rate', int, 0, requires_spell_or_weapon),
    ItemComponent('level', 'Weapon Level Required', 'WeaponRank', None, requires_spell_or_weapon),
    ItemComponent('weight', 'Weight', int, 0, requires_spell_or_weapon),
    ItemComponent('crit', 'Critical Rate', int, 0, requires_spell_or_weapon),
    ItemComponent('magic', 'Magical', bool, False, requires_spell_or_weapon),
    ItemComponent('exp', 'Custom Experience', int, 10, requires_aspect),
    ItemComponent('wexp', 'Custom Weapon Experience', int, 1, requires_spell_or_weapon),

    ItemComponent('uses', 'Total Uses', int, 30, requires_aspect, volatile=True),
    ItemComponent('c_uses', 'Uses per Chapter', int, 8, requires_aspect, volatile=True),
    ItemComponent('hp_cost', 'Costs HP', int, 0, requires_aspect),
    ItemComponent('mana_cost', 'Costs Mana', int, 0, requires_aspect),
    # ItemComponent('cooldown', 'Cooldown', int, 0, requires_aspect, volatile=True),
    
    ItemComponent('heal_on_hit', 'Heals Target', int, 0, requires_spell_or_weapon),
    ItemComponent('heal_on_use', 'Heal on Use', int, 10, requires_usable),

    ItemComponent('effective', 'Effective Against', EffectiveSubComponent, EffectiveData(), requires_spell_or_weapon),
    ItemComponent('prf_unit', 'Restricted to (Unit)', BasicSubComponent, PrfUnitData(), requires_aspect),
    ItemComponent('prf_class', 'Restricted to (Class)', BasicSubComponent, PrfClassData(), requires_aspect),
    ItemComponent('prf_tag', 'Restricted to (Tag)', BasicSubComponent, PrfTagData(), requires_aspect),

    ItemComponent('locked', 'Cannot be removed from Unit'),
    ItemComponent('brave', 'Brave', 'BraveChoice', 0, requires_spell_or_weapon),
    ItemComponent('reverse', 'Reverses Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('double_triangle', 'Doubles Effect of Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('cannot_be_countered', 'Cannot be Countered', bool, False, requires_weapon),
    ItemComponent('no_double', 'Cannot Double', bool, False, requires_weapon),
    ItemComponent('ignore_triangle', 'Ignores Weapon Triangle', bool, False, requires_spell_or_weapon),
    ItemComponent('damage_on_miss', 'Does %% Damage even on Miss', float, 0.5, requires_might_and_hit),
    ItemComponent('lifelink', 'Heals user %% of Damage Dealt', float, 0.5, requires_might),
    ItemComponent('unrepairable', 'Cannot be Repaired', bool, False, requires_uses),

    ItemComponent('aoe', 'Area of Effect', (AOEMode, SpellTarget, int), (AOEMode.Normal, SpellTarget.Unit, 0), requires_spell_or_weapon),

    ItemComponent('promotion', 'Promotes (Class)', BasicSubComponent, PromoteData(), requires_usable),
    ItemComponent('class_change', 'Changes (Class)', BasicSubComponent, ClassChangeData(), requires_usable),
    ItemComponent('permanent_stat_increase', 'Permanently Increases (Stat)', StatChangeSubComponent, StatChangeData(), requires_usable),
    ItemComponent('permanent_growth_increase', 'Permanently Increases (Growth)', GrowthChangeSubComponent, GrowthChangeData(), requires_usable),

    ItemComponent('custom_damage_equation', 'Custom Damage Equation', 'Equation', None, requires_might),
    ItemComponent('custom_defense_equation', 'Custom Defense Equation', 'Equation', None, requires_might),
    ItemComponent('custom_hit_equation', 'Custom Hit Equation', 'Equation', None, requires_hit),
    ItemComponent('custom_avoid_equation', 'Custom Avoid Equation', 'Equation', None, requires_hit),
    ItemComponent('custom_crit_equation', 'Custom Crit Equation', 'Equation', None, requires_crit),
    ItemComponent('custom_dodge_equation', 'Custom Crit Avoid Equation', 'Equation', None, requires_crit),
    ItemComponent('custom_double_atk_equation', 'Custom Double Attack Equation', 'Equation', None, requires_weapon),
    ItemComponent('custom_double_def_equation', 'Custom Double Defense Equation', 'Equation', None, requires_weapon),

    # ItemComponent('hit_status', 'Applies Status on hit', 'Status', None, requires_spell_or_weapon),
    # ItemComponent('use_status', 'Applies Status on use', 'Status', None, requires_usable),
    # ItemComponent('equip_status', 'Applies Status while equipped', 'Status', None, requires_weapon),
    # ItemComponent('hold_status', 'Applies Status while held', 'Status', None),

    # ItemComponent('movement_hit', 'Applies Movement on hit', 'Movement', None, requires_spell_or_weapon),
    # ItemComponent('movement_self_hit', 'Applies Movement to self on hit', 'Movement', None, requires_spell_or_weapon),
    # ItemComponent('movement_use', 'Applies Movement on use', 'Movement', None, requires_usable),

    ItemComponent('repair', 'Repairs Items', bool, True, repair_requires),
    # ItemComponent('target_restrict', 'Restrict Targets', 'Eval', '', requires_aspect),
    ItemComponent('multiple_targets', 'Multiple Targets', TargetSubComponent, TargetData(), requires_spell),
    # ItemComponent('multiple_target_restrict', 'Restrict Multiple Targets', 'Eval', '', requires_multiple_targets)
    # ItemComponent('interact', 'Interact with Event Tile', ??, None, requires_spell),
    # ItemComponent('event_on_use', ??)
    # ItemComponent('event_on_hit', ??)

    ItemComponent('no_ai', 'AI will not use', bool, True, requires_aspect),
    # ItemComponent('ai_target', 'Restrict AI Targets', 'Eval', '', requires_aspect),
    # ItemComponent('warning', 'Show Warning', 'Eval', '', requires_spell_or_weapon),

    ItemComponent('map_hit_color', 'Map Hit Color', 'Color', (255, 255, 255, 120), requires_aspect),
    # ItemComponent('aoe_anim', 'Custom AOE Map Animation', 'Animation', None, requires_aspect),
    # ItemComponent('target_anim', 'Custom Map Animation on target', 'Animation', None, requires_aspect),
    # ItemComponent('self_anim', 'Custom Map Animation on user', 'Animation', None, requires_aspect),
    # ItemComponent('custom_sfx', 'Custom Sound', 'Sound', None, requires_aspect),
    # ItemComponent('combat_effect', 'Custom Effect in Animation Combat', 'Effect', None, requires_weapon),
    # ItemComponent('custom_anim', 'Custom Combat Animation', 'Combat Anim', None, requires_aspect)

])

def get_component(nid):
    base = item_components.get(nid)
    return ItemComponent.copy(base)

def deserialize_component(dat):
    nid, value = dat
    base = item_components.get(nid)
    copy = ItemComponent.copy(base)
    if copy.attr in (EffectiveSubComponent, BasicSubComponent, StatChangeSubComponent, GrowthChangeSubComponent, TargetSubComponent):
        for v in value:
            deserialized = copy.attr.deserialize(v)
            copy.value.append(deserialized)
    else:
        copy.value = value
    return copy
