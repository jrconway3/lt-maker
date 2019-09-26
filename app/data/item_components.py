from enum import Enum
from collections import namedtuple

from app.data.weapons import WeaponRank, WeaponType

from app.data.database import database as DB

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

def requires_spell_or_weapon(other_components):
    return 'weapon' in other_components or 'spell' in other_components

def requires_usable(self, other_components):
    return 'usable' in other_components

item_component = namedtuple('ItemComponent', 
                            ['nid', 'name', 'attr', 'value', 'requires'],
                            defaults=[None, '', bool, True, no_requirement])

item_components = {
    'weapon': item_component('weapon', 'Weapon', WeaponType, DB.weapons[0],
                             lambda x: 'spell' not in x),
    'spell': item_component('spell', 'Spell', (WeaponType, SpellAffect, SpellTarget),
                            (DB.weapons[0], SpellAffect.Neutral, SpellTarget.Unit),
                            lambda x: 'weapon' not in x),
    'usable': item_component('usable', 'Usable'),
    'might': item_component('might', 'Might', int, 0, requires_spell_or_weapon),
    'hit': item_component('hit', 'Hit Rate', int, 0, requires_spell_or_weapon),
    'level': item_component('level', 'Weapon Level Required', WeaponRank, DB.weapon_ranks[0], requires_spell_or_weapon),
    'uses': item_component('uses', 'Total Uses', int, 30),
    'c_uses': item_component('c_uses', 'Uses per Chapter', int, 8),
    'weight': item_component('weight', 'Weight', int, 0, requires_spell_or_weapon),
    'crit': item_component('crit', 'Critical Rate', int, 0, requires_spell_or_weapon),
    'heal_on_hit': item_component('heal_on_hit', 'Heal on Hit', int, 0, requires_spell_or_weapon),
    'heal_on_use': item_component('heal_on_use', 'Heal on Use', int, 10, requires_usable)
}

def get_component(nid):
    return item_components[nid]
