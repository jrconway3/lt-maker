from collections import Counter

from app.data.data import Prefab
from app.data.database import DB

class Multiset(Counter):
    def __contains__(self, item):
        return self[item] > 0

# Main unit object used by engine
class UnitObject(Prefab):
    def __init__(self, prefab):
        self.nid = prefab.nid
        self.position = self.previous_position = prefab.starting_position
        self.team = prefab.team
        self.party = 0
        self.klass = prefab.klass
        self.gender = prefab.gender
        self.level = prefab.level
        self.exp = 0
        self.generic = prefab.generic

        self.ai = prefab.ai

        self.items = self.create_items(prefab.starting_items)

        if self.generic:
            self.faction = prefab.faction
            self.name = DB.factions.get(self.faction).name
            self.desc = DB.factions.get(self.faction).desc
            self.tags = []
            self.stats = {stat.nid: stat.value for stat in DB.classes.get(self.klass).bases}
            self.growths = {stat.nid: stat.value for stat in DB.classes.get(self.klass).growths}
            self.wexp = {weapon.nid: 0 for weapon in DB.weapons}
            self.calculate_needed_wexp_from_items()
            self.portrait_nid = None
        else:
            self.faction = None
            self.name = prefab.name
            self.desc = prefab.desc
            self.tags = [tag for tag in prefab.tags]
            self.stats = {stat.nid: stat.value for stat in prefab.bases}
            self.growths = {stat.nid: stat.value for stat in prefab.growths}
            self.wexp = {weapon.nid: weapon.wexp_gain for weapon in prefab.wexp_gain}
            self.portrait_nid = prefab.portrait_nid
        self.growth_points = {k: 50 for k in self.stats.keys()}

        self.status_effects = []
        self.status_bundle = Multiset()

        # TODO -- change these to use equations
        self.current_hp = self.stats.get('HP')
        self.current_mana = self.stats.get('MAG')
        self.movement_left = self.stats.get('MOV')

        self.traveler = None

        # -- Other properties
        self.dead = False
        self.is_dying = False
        self._finished = False
        self._has_attacked = False
        self._has_traded = False
        self._has_moved = False

        self.sprite = None
        self.battle_anim = None

        self.current_move = None  # Holds the move action the unit last used
        # Maybe move to movement manager?

    def create_items(self, item_nid_list):
        items = []
        for item_nid, droppable in item_nid_list:
            item = DB.items.get_instance(item_nid)
            item.owner_nid = self.nid
            item.droppable = droppable
            items.append(item)
        return items

    def calculate_needed_wexp_from_items(self):
        for item in self.items:
            if item.level:
                if item.weapon:
                    weapon_type = item.weapon.value
                elif item.spell:
                    weapon_type = item.spell.value[0]
                requirement = DB.weapon_ranks.get(item.level.value).requirement
                self.wexp[weapon_type] = max(self.wexp[weapon_type], requirement)

    def can_wield(self, item):
        if (item.weapon or item.spell) and item.level:
            weapon_rank = DB.weapon_ranks.get(item.level.value)
            req = weapon_rank.requirement
            comp = item.weapon.value if item.weapon else item.spell.value[0]
            spec_wexp = self.wexp.get(comp)
            klass = DB.classes.get(self.klass)
            klass_usable = klass.wexp_gain.get(comp).usable
            if klass_usable and spec_wexp >= req:
                return True
            return False
        elif item.prf_self:
            if self.nid in item.prf_unit.value.keys():
                return True
            else:
                return False
        elif item.prf_class:
            if self.klass in item.prf_class.value.keys():
                return True
            else:
                return False
        else:
            return True

    def get_weapon(self):
        for item in self.items:
            if item.weapon and self.can_wield(item):
                return item
        return None

    def get_spell(self):
        for item in self.items:
            if item.spell and self.can_wield(item):
                return item
        return None

    def has_canto(self):
        return 'canto' in self.status_bundle or 'canto_plus' in self.status_bundle

    def has_canto_plus(self):
        return 'canto_plus' in self.status_bundle

    @property
    def finished(self):
        return self._finished

    @property
    def has_attacked(self):
        return self._finished or self._has_attacked

    @property
    def has_traded(self):
        return self._finished or self._has_attacked or self._has_traded

    @property
    def has_moved(self):
        return self._finished or self._has_attacked or self._has_traded or self._has_moved

    @finished.setter
    def finished(self, val):
        self._finished = val

    @has_attacked.setter
    def has_attacked(self, val):
        self._has_attacked = val

    @has_traded.setter
    def has_traded(self, val):
        self._has_traded = val

    @has_moved.setter
    def has_moved(self, val):
        self._has_moved = val

    def get_action_state(self):
        return (self._finished, self._has_attacked, self._has_traded, self._has_moved)

    def set_action_state(self, state):
        self._finished = state[0]
        self._has_attacked = state[1]
        self._has_traded = state[2]
        self._has_moved = state[3]

    def reset(self):
        self._finished = False
        self._has_attacked = False
        self._has_traded = False
        self._has_moved = False
