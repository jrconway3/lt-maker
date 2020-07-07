from app import utilities
from app.data.data import Prefab
from app.data.database import DB

from app.engine.game_state import game

# Main unit object used by engine
class UnitObject(Prefab):
    @classmethod
    def from_prefab(cls, prefab):
        self = cls()
        self.nid = prefab.nid
        self.position = self.previous_position = prefab.starting_position
        self.team = prefab.team
        self.party = 0
        self.klass = prefab.klass
        self.variant = prefab.variant
        self.level = prefab.level
        self.exp = 0
        self.generic = prefab.generic

        self.ai = prefab.ai
        self.ai_group = 0

        self.items = self.create_items(prefab.starting_items)

        if self.generic:
            self.faction = prefab.faction
            self.name = DB.factions.get(self.faction).name
            self.desc = DB.factions.get(self.faction).desc
            self._tags = []
            self.stats = {stat.nid: stat.value for stat in DB.classes.get(self.klass).bases}
            self.growths = {stat.nid: stat.value for stat in DB.classes.get(self.klass).growths}
            self.wexp = {weapon.nid: 0 for weapon in DB.weapons}
            self.calculate_needed_wexp_from_items()
            self.portrait_nid = None
        else:
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

        self.current_hp = game.equations.hitpoints(self)
        if 'MANA' in DB.equations:
            self.current_mana = game.equations.mana(self)
        else:
            self.current_mana = 0
        self.movement_left = game.equations.movement(self)

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

    def set_hp(self, val):
        self.current_hp = utilities.clamp(val, 0, game.equations.hitpoints(self))

    def get_mana(self):
        return self.current_mana

    def set_mana(self, val):
        self.current_mana = utilities.clamp(val, 0, game.equations.mana(self))

    def get_exp(self):
        return self.exp

    def set_exp(self, val):
        self.exp = int(val)

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

    def calculate_needed_wexp_from_items(self):
        for item in self.items:
            if item.level:
                if item.weapon:
                    weapon_type = item.weapon.value
                elif item.spell:
                    weapon_type = item.spell.value[0]
                requirement = DB.weapon_ranks.get(item.level.value).requirement
                self.wexp[weapon_type] = max(self.wexp[weapon_type], requirement)

    def has_uses(self, item) -> bool:
        if item.uses and item.uses.value <= 0:
            return False
        if item.c_uses and item.c_uses.value <= 0:
            return False
        if item.hp_cost and self.get_hp() <= item.hp_cost.value:
            return False
        if item.mana_cost and self.get_mana() <= item.mana_cost.value:
            return False
        return True

    def could_wield(self, item) -> bool:
        if item.prf_unit:
            if self.nid not in item.prf_unit.value.keys():
                return False
        if item.prf_class:
            if self.klass not in item.prf_class.value.keys():
                return False
        if item.prf_tag:
            if not any(tag in item.prf_tag.value.keys() for tag in self.tags):
                return False
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
        return True

    def can_wield(self, item) -> bool:
        return self.could_wield(item) and self.has_uses(item)

    def could_use(self, item):
        if item.heal:
            if self.get_hp() < game.equations.hitpoints(self):
                return True
        if item.mana:
            if self.get_mana() < game.equations.mana(self):
                return True
        if item.permanent_stat_increase:
            for stat_nid, increase in item.permanent_stat_increase.value.items():
                current_value = self.stats[stat_nid]
                klass_max = DB.classes.get(self.klass).max_stats.get(stat_nid)
                if current_value < klass_max:
                    return True
        if item.promotion:
            klass = DB.classes.get(self.klass)
            allowed_classes = item.promotion.value
            max_level = klass.max_level
            if self.level >= max_level//2 and len(klass.turns_into) >= 1 and \
                    (klass in allowed_classes or 'All' in allowed_classes):
                return True
        if not item.heal or item.mana or item.permanent_stat_increase or item.promotion:
            return True
        return False

    def can_use(self, item) -> bool:
        return self.could_use(item) and self.has_uses(item)

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

    def equip(self, item):
        if item in self.items and self.items.index(item) == 0:
            return  # Don't need to do anything
        self.insert_item(0, item)

    def add_item(self, item):
        index = len(self.items)
        self.insert_item(index, item)

    def unequip_item(self, item):
        # handle status on equip
        pass

    def equip_item(self, item):
        # handle status on equip
        pass

    def insert_item(self, index, item):
        def handle_equip(item):
            if self.get_weapon() == item:
                # You unequipped a different item, so remove its status
                if len(self.items) > 1 and self.could_wield(self.items[1]):
                    self.unequip_item(self.items[1])
                # Now add yours
                if self.can_wield(item):
                    self.equip_item(item)

        if item in self.items:
            self.items.remove(item)
            self.items.insert(index, item)
            handle_equip(item)
        else:
            self.items.insert(index, item)
            item.owner_nid = self.nid
            # Statuses here
            handle_equip(item)

    def remove_item(self, item):
        next_weapon = next((item for item in self.items if item.weapon and self.could_wield(item)), None)
        was_main_weapon = next_weapon == item
        self.items.remove(item)
        item.owner_nid = None
        if was_main_weapon:
            self.unequip_item(item)
        # Status effects
        # There may be a new item equipped
        if was_main_weapon and self.get_weapon():
            self.equip_item(self.get_weapon())

    def get_internal_level(self):
        klass = DB.classes.get(self.klass)
        if klass.tier == 0:
            return self.level - klass.max_level
        elif klass.tier == 1:
            return self.level
        else:
            running_total = self.level
            # Need do while
            counter = 5
            while counter > 0:
                counter -= 1  # Just to make sure no infinte loop
                promotes_from = klass.promotes_from
                if promotes_from:
                    klass = DB.classes.get(promotes_from)
                    running_total += klass.max_level
                else:
                    return running_total
                if klass.tier <= 0:
                    return running_total
            return running_total 

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

    def clean_up(self):
        if self.traveler:
            self.traveler = None
            # Remove rescue penalty

        self.set_hp(1000)  # Set to full health

        # TODO remove temporary statuses
        self.position = None
        if self.sprite:
            self.sprite.change_state('normal')
        self.reset()

    def serialize(self):
        s_dict = {'nid': self.nid,
                  'position': self.position,
                  'team': self.team,
                  'party': self.party,
                  'klass': self.klass,
                  'variant': self.variant,
                  'faction': self.faction,
                  'level': self.level,
                  'exp': self.exp,
                  'generic': self.generic,
                  'ai': self.ai,
                  'ai_group': self.ai_group,
                  'items': [item.uid for item in self.items],
                  'name': self.name,
                  'desc': self.desc,
                  'tags': self._tags,
                  'stats': self.stats,
                  'growths': self.growths,
                  'growth_points': self.growth_points,
                  'starting_position': self.starting_position,
                  'wexp': self.wexp,
                  'portrait_nid': self.portrait_nid,
                  'status_effects': [status.uid for status in self.status_effects],
                  'current_hp': self.current_hp,
                  'current_mana': self.current_mana,
                  'traveler': self.traveler,
                  'dead': self.dead,
                  'finished': self._finished,
                  }
        return s_dict

    @classmethod
    def deserialize(cls, s_dict):
        self = cls()
        self.nid = s_dict['nid']
        self.position = self.previous_position = s_dict['position']
        self.team = s_dict['team']
        self.party = s_dict['party']
        self.klass = s_dict['klass']
        self.variant = s_dict['variant']
        self.level = s_dict['level']
        self.exp = s_dict['exp']
        self.generic = s_dict['generic']

        self.ai = s_dict['ai']
        self.ai_group = s_dict['ai_group']

        self.items = [game.get_item(item_uid) for item_uid in s_dict['items']]

        self.faction = s_dict['faction']
        self.name = s_dict['name']
        self.desc = s_dict['desc']
        self._tags = s_dict['tags']
        self.stats = s_dict['stats']
        self.growths = s_dict['growths']
        self.growth_points = s_dict['growth_points']
        self.wexp = s_dict['wexp']
        self.portrait_nid = s_dict['portrait_nid']
        self.starting_position = self.position

        self.status_effects = [game.get_status(status_uid) for status_uid in s_dict['status_effects']]
        self.status_bundle = Multiset()

        self.current_hp = s_dict['current_hp']
        self.current_mana = s_dict['current_mana']
        self.movement_left = game.equations.movement(self)

        self.traveler = s_dict['traveler']

        # -- Other properties
        self.dead = s_dict['dead']
        self.is_dying = False
        self._finished = s_dict['finished']
        self._has_attacked = False
        self._has_traded = False
        self._has_moved = False

        self.sprite = None
        self.sound = None
        self.battle_anim = None

        self.current_move = None  # Holds the move action the unit last used
        # Maybe move to movement manager?
        return self
