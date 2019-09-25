from enum import Enum

from app.data.weapons import WeaponRank, WeaponType

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

class ItemComponent(object):
    nid = None
    name = ''
    attr = bool

    def requires(self, other_components):
        return True

def requires_spell_or_weapon(self, other_components):
    return 'weapon' in other_components or 'spell' in other_components

def requires_usable(self, other_components):
    return 'usable' in other_components

class Weapon(ItemComponent):
    nid = 'weapon'
    name = 'Weapon'
    attr = WeaponType

    def requires(self, other_components):
        return 'spell' not in other_components

class Spell(ItemComponent):
    nid = 'spell'
    name = 'Spell'
    attr = (WeaponType, SpellAffect, SpellTarget)

    def requires(self, other_components):
        return 'weapon' not in other_components

class Usable(ItemComponent):
    nid = 'usable'
    name = 'Usable'

class Might(ItemComponent):
    nid = 'might'
    name = 'Might'
    attr = int
    requires = requires_spell_or_weapon

class Hit(ItemComponent):
    nid = 'hit'
    name = 'Hit'
    attr = int
    requires = requires_spell_or_weapon

class WeaponLevel(ItemComponent):
    nid = 'level'
    name = 'Weapon Level Required'
    attr = WeaponRank
    requires = requires_spell_or_weapon

class Uses(ItemComponent):
    nid = 'uses'
    name = 'Total Uses'
    attr = int

class ChapterUses(ItemComponent):
    nid = 'c_uses'
    name = 'Uses per Chapter'
    attr = int

class Weight(ItemComponent):
    nid = 'weight'
    name = 'Weight'
    attr = int
    requires = requires_spell_or_weapon

class Crit(ItemComponent):
    nid = 'crit'
    name = 'Crit. Rate'
    attr = int
    requires = requires_spell_or_weapon

class HealOnHit(ItemComponent):
    nid = 'heal_on_hit'
    name = "Heal on Hit"
    attr = int
    requires = requires_spell_or_weapon

class HealOnUse(ItemComponent):
    nid = 'heal_on_uses'
    name = 'Heal on Use'
    attr = int
    requires = requires_usable
