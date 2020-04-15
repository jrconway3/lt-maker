from enum import Enum

from app.data.data import Data, Prefab

# Custom Types
class SpellAffect(Enum):
    Helpful = 1
    Neutral = 2
    Harmful = 3

class SpellTarget(Enum):
    Ally = 1
    Enemy = 2
    Unit = 3
    Tile = 4
    TileWithoutUnit = 5

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

class RestrictedSubComponent(Prefab):
    def __init__(self, nid):
        self.nid: str = nid

    def serialize(self):
        return self.nid

    @classmethod
    def deserialize(cls, s):
        self = cls(s)
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

class PrfUnitData(Data):
    datatype = RestrictedSubComponent

    def add_new_default(self, DB):
        for unit in DB.units:
            if unit.nid not in self.keys():
                nid = unit.nid
                break
        else:
            nid = DB.units[0].nid
        self.append(RestrictedSubComponent(nid))

class PrfClassData(Data):
    datatype = RestrictedSubComponent

    def add_new_default(self, DB):
        for klass in DB.classes:
            if klass.nid not in self.keys():
                nid = klass.nid
                break
        else:
            nid = DB.classes[0].nid
        self.append(RestrictedSubComponent(nid))

class ItemComponent(object):
    def __init__(self, nid=None, name='', attr=bool, value=True, requires=no_requirement):
        self.nid = nid
        self.name = name
        self.attr = attr
        self.value = value
        self.requires = requires

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
            return self.nid, [v.serialize() for v in self.value]
        else:
            return (self.nid, self.value)

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
    ItemComponent('wexp', 'Custom Weapon Experience', int, 1, requires_spell_or_weapon),

    ItemComponent('uses', 'Total Uses', int, 30),
    ItemComponent('c_uses', 'Uses per Chapter', int, 8),
    
    ItemComponent('heal_on_hit', 'Heals Target', int, 0, requires_spell_or_weapon),
    ItemComponent('heal_on_use', 'Heal on Use', int, 10, requires_usable),

    ItemComponent('effective', 'Effective Against', EffectiveSubComponent, EffectiveData(), requires_spell_or_weapon),
    ItemComponent('prf_unit', 'Restricted to (Unit)', RestrictedSubComponent, PrfUnitData(), requires_aspect),
    ItemComponent('prf_class', 'Restricted to (Class)', RestrictedSubComponent, PrfClassData(), requires_aspect)
])

def get_component(nid):
    base = item_components.get(nid)
    return ItemComponent.copy(base)

def deserialize_component(dat):
    nid, value = dat
    base = item_components.get(nid)
    copy = ItemComponent.copy(base)
    if copy.attr in (EffectiveSubComponent, RestrictedSubComponent):
        for v in value:
            deserialized = copy.attr.deserialize(v)
            copy.value.append(deserialized)
    else:
        copy.value = value
    return copy
