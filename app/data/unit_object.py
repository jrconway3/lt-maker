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
            self.wexp = {weapon.nid: prefab.wexp_gain for weapon in prefab.wexp_gain}
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
        self.finished = False
        self.has_acted = False
        self.has_subacted = False
        self.has_moved = False

        self.sprite = None
        self.battle_anim = None

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
                self.wexp[weapon_type] = min(self.wexp[weapon_type], requirement)
