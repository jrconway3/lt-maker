from app import utilities
from app.data.data import Prefab
from app.data.database import DB

# Main unit object used by engine
class SimpleUnitObject(Prefab):
    @classmethod
    def from_prefab(cls, prefab, parser):
        self = cls()
        self.nid = prefab.nid
        self.position = self.previous_position = (0, 0)
        self.team = 'player'
        self.party = 0
        self.klass = prefab.klass
        self.variant = prefab.variant
        self.level = prefab.level
        self.exp = 0
        self.generic = False

        self.ai = DB.ai[0]
        self.ai_group = 0

        self.items = self.create_items(prefab.starting_items)

        self.faction = None
        self.name = prefab.name
        self.desc = prefab.desc
        self._tags = [tag for tag in prefab.tags]
        self.stats = {stat.nid: stat.value for stat in prefab.bases}
        self.growths = {stat.nid: stat.value for stat in prefab.growths}
        self.wexp = {weapon.nid: weapon.wexp_gain for weapon in prefab.wexp_gain}
        self.portrait_nid = prefab.portrait_nid
        self.starting_position = self.position
            
        if DB.constants.get('player_leveling').value == 'Fixed':
            self.growth_points = {k: 50 for k in self.stats.keys()}
        else:
            self.growth_points = {k: 0 for k in self.stats.keys()}

        self.status_effects = []
        self.status_bundle = utilities.Multiset()

        self.current_hp = parser.hitpoints(self)
        if 'MANA' in DB.equations:
            self.current_mana = parser.mana(self)
        else:
            self.current_mana = 0
        self.movement_left = parser.movement(self)

        self.traveler = None

        # -- Other properties
        self.dead = False
        self.is_dying = False
        self._finished = False
        self._has_attacked = False
        self._has_traded = False
        self._has_moved = False

        self.sprite = None
        self.sound = None
        self.battle_anim = None

        self.current_move = None  # Holds the move action the unit last used
        # Maybe move to movement manager?
        return self

    def get_hp(self):
        return self.current_hp

    def get_mana(self):
        return self.current_mana

    def get_exp(self):
        return self.exp

    @property
    def tags(self):
        unit_tags = self._tags
        class_tags = DB.classes.get(self.klass).tags
        return unit_tags + class_tags

    def create_items(self, item_nid_list):
        items = []
        for item_nid, droppable in item_nid_list:
            item = DB.items.get_instance(item_nid)
            item.owner_nid = self.nid
            item.droppable = droppable
            items.append(item)
        return items
