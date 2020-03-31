from enum import Enum

from app.data.data import Data

# Custom Types
class SpellAffect(Enum):
    Beneficial = 1
    Neutral = 2
    Detrimental = 3

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

class item_component(object):
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
        return (self.nid, self.value)

item_components = Data([
    item_component('weapon', 'Weapon', 'WeaponType', None,
                             lambda x: 'spell' not in x),
    item_component('spell', 'Spell', ('WeaponType', SpellAffect, SpellTarget),
                            (None, SpellAffect.Neutral, SpellTarget.Unit),
                            lambda x: 'weapon' not in x),
    item_component('usable', 'Usable'),
    item_component('might', 'Might', int, 0, requires_spell_or_weapon),
    item_component('hit', 'Hit Rate', int, 0, requires_spell_or_weapon),
    item_component('level', 'Weapon Level Required', 'WeaponRank', None, requires_spell_or_weapon),
    item_component('weight', 'Weight', int, 0, requires_spell_or_weapon),
    item_component('crit', 'Critical Rate', int, 0, requires_spell_or_weapon),
    item_component('magic', 'Magical', bool, False, requires_spell_or_weapon),
    item_component('wexp', 'Weapon Experience Gained', int, 1, requires_spell_or_weapon),

    item_component('uses', 'Total Uses', int, 30),
    item_component('c_uses', 'Uses per Chapter', int, 8),
    
    item_component('heal_on_hit', 'Heal on Hit', int, 0, requires_spell_or_weapon),
    item_component('heal_on_use', 'Heal on Use', int, 10, requires_usable)
])

def get_component(nid):
    base = item_components.get(nid)
    return item_component.copy(base)

def deserialize_component(dat):
    nid, value = dat
    base = item_components.get(nid)
    copy = item_component.copy(base)
    copy.value = value
    return copy
