import time
import random
from collections import Counter

from app.constants import VERSION
from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine import state_machine, static_random
from app.engine import config as cf

import logging
logger = logging.getLogger(__name__)

class GameState():
    def __init__(self):
        self.clear()

    def clear(self):
        self.game_vars = Counter()
        self.memory = {}

        self.state = state_machine.StateMachine()

        self.playtime = 0

        self.alerts = []
        self.cursor = None
        self.camera = None

        self.current_level = None

    def load_states(self, starting_states):
        self.state.load_states(starting_states)

    # Start a new game
    # When the player clicks "New Game"
    def build_new(self):
        from app.engine import records
        logger.info("Building New Game")
        self.playtime = 0

        self.unit_registry = {}
        self.item_registry = {}
        self.skill_registry = {}
        self.terrain_status_registry = {}

        self.parties = {}
        self.current_party = None
        self.current_level = None
        self.game_vars.clear()

        # Set up random seed
        if cf.SETTINGS['random_seed'] >= 0:
            random_seed = int(cf.SETTINGS['random_seed'])
        else:
            random_seed = random.randint(0, 1023)
        static_random.set_seed(random_seed)
        self.game_vars['_random_seed'] = random_seed

        # Set up overworld  TODO
        if DB.constants.value('overworld'):
            self.overworld = None
        else:
            self.overworld = None

        self.records = records.Recordkeeper()
        self.market_items = []
        self.unlocked_lore = []
        self.already_triggered_events = []
        self.sweep()
        self.generic()

    def sweep(self):
        """
        Cleans up variables that need to be reset at the end of each level
        """
        from app.engine import turnwheel
        from app.events import event_manager
        self.level_vars = Counter()
        self.turncount = 0
        self.talk_options = []
        self.base_convos = {}
        self.action_log = turnwheel.ActionLog()
        self.events = event_manager.EventManager()

    def generic(self):
        """
        Done on loading a level, whether from overworld, last level, save_state, etc.
        """
        from app.engine import cursor, camera, phase, highlight, \
            movement, death, ai_controller, map_view, ui_view
        # Systems
        self.cursor = cursor.Cursor()
        self.camera = camera.Camera()
        self.phase = phase.PhaseController()
        self.highlight = highlight.HighlightController()
        self.map_view = map_view.MapView()
        self.movement = movement.MovementManager()
        self.death = death.DeathManager()
        self.ui_view = ui_view.UIView()
        self.combat_instance = []
        self.exp_instance = []
        self.ai = ai_controller.AIController()

        self.alerts.clear()

        # Build registries
        self.map_sprite_registry = {}

    def start_level(self, level_nid, with_party=None):
        """
        Done at the beginning of a new level to start the level up
        """
        self.generic()
        logging.debug("Starting Level %s", level_nid)
        
        from app.engine.objects.level import LevelObject
        from app.engine.objects.tilemap import TileMapObject
        from app.engine.objects.party import PartyObject

        level_nid = str(level_nid)
        level_prefab = DB.levels.get(level_nid)
        tilemap_nid = level_prefab.tilemap
        tilemap_prefab = RESOURCES.tilemaps.get(tilemap_nid)
        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        self.current_level = LevelObject.from_prefab(level_prefab, tilemap, self.unit_registry)
        if with_party:
            self.current_party = with_party
        else:
            self.current_party = self.current_level.party

        # Build party object for new parties
        if self.current_party not in self.parties:
            party_prefab = DB.parties.get(self.current_party)
            if not party_prefab:
                party_prefab = DB.parties[0]
            nid, name, leader = party_prefab.nid, party_prefab.name, party_prefab.leader
            self.parties[self.current_party] = PartyObject(nid, name, leader)

        # Assign every unit the levels party if they don't already have one
        for unit in self.current_level.units:
            if not unit.party:
                unit.party = self.current_party
        self.set_up_game_board(self.current_level.tilemap)

        for unit in self.current_level.units:
            self.full_register(unit)
        for unit in self.current_level.units:
            self.arrive(unit)

    def full_register(self, unit):
        self.register_unit(unit)
        for item in unit.items:
            self.register_item(item)
        for skill in unit.skills:
            self.register_skill(skill)

    def set_up_game_board(self, tilemap):
        from app.engine import game_board, boundary
        self.board = game_board.GameBoard(tilemap)
        self.boundary = boundary.BoundaryInterface(tilemap.width, tilemap.height)

    def save(self):
        self.action_log.record = False
        # Units need to leave before saving -- this is so you don't 
        # have to save region and terrain statuses
        if self.current_level:
            for unit in self.units:
                if unit.position:
                    self.leave(unit, True)

        s_dict = {'units': [unit.save() for unit in self.unit_registry.values()],
                  'items': [item.save() for item in self.item_registry.values()],
                  'skills': [skill.save() for skill in self.skill_registry.values()],
                  'terrain_status_registry': self.terrain_status_registry,
                  'level': self.current_level.save() if self.current_level else None,
                  'turncount': self.turncount,
                  'playtime': self.playtime,
                  'game_vars': self.game_vars,
                  'level_vars': self.level_vars,
                  'parties': [party.save() for party in self.parties.values()],
                  'current_party': self.current_party,
                  'state': self.state.save(),
                  'action_log': self.action_log.save(),
                  'events': self.events.save(),
                  'records': self.records.save(),
                  'market_items': self.market_items,  # Item nids
                  'unlocked_lore': self.unlocked_lore,
                  'already_triggered_events': self.already_triggered_events,
                  'talk_options': self.talk_options,
                  'base_convos': self.base_convos,
                  'current_random_state': static_random.get_combat_random_state()
                  }
        meta_dict = {'playtime': self.playtime,
                     'realtime': time.time(),
                     'version': VERSION,
                     'title': DB.constants.value('title'),
                     }
        if self.current_level:
            meta_dict['level_title'] = self.current_level.name
            meta_dict['level_nid'] = self.current_level.nid
        elif self.game_vars.get('_next_level_nid'):
            fake_level = DB.levels.get(self.game_vars.get('_next_level_nid'))
            meta_dict['level_title'] = fake_level.name
            meta_dict['level_nid'] = fake_level.nid
        else:
            meta_dict['level_title'] = 'Overworld'
            meta_dict['level_nid'] = None

        # Now have units actually arrive on map
        if self.current_level:
            for unit in self.units:
                if unit.position:
                    self.arrive(unit, True)

        self.action_log.record = True
        return s_dict, meta_dict

    def load(self, s_dict):
        from app.engine import turnwheel, records
        from app.events import event_manager

        from app.engine.objects.item import ItemObject
        from app.engine.objects.skill import SkillObject
        from app.engine.objects.unit import UnitObject
        from app.engine.objects.level import LevelObject
        from app.engine.objects.party import PartyObject

        logger.info("Loading Game...")
        self.game_vars = Counter(s_dict.get('game_vars', {}))
        static_random.set_seed(self.game_vars.get('_random_seed', 0))
        self.level_vars = Counter(s_dict.get('level_vars', {}))
        self.playtime = float(s_dict['playtime'])
        self.parties = {party_data['nid']: PartyObject.restore(party_data) for party_data in s_dict['parties']}
        self.current_party = s_dict['current_party']
        self.turncount = int(s_dict['turncount'])

        self.state.load_states(s_dict['state'][0], s_dict['state'][1])

        self.item_registry = {item['uid']: ItemObject.restore(item) for item in s_dict['items']}
        self.skill_registry = {skill['uid']: SkillObject.restore(skill) for skill in s_dict['skills']}
        self.terrain_status_registry = s_dict.get('terrain_status_registry', {})
        self.unit_registry = {unit['nid']: UnitObject.restore(unit) for unit in s_dict['units']}
        # Handle subitems
        for item in self.item_registry.values():
            for subitem_uid in item.subitem_uids:
                subitem = self.item_registry.get(subitem_uid)
                item.subitems.append(subitem)
                subitem.parent_item = item
        # Handle subskill
        for skill in self.skill_registry.values():
            if skill.subskill_uid is not None:
                subskill = self.skill_registry.get(skill.subskill_uid)
                skill.subskill = subskill
                subskill.parent_skill = skill

        self.market_items = s_dict.get('market_items', [])
        self.unlocked_lore = s_dict.get('unlocked_lore', [])
        self.already_triggered_events = s_dict.get('already_triggered_events', [])
        self.talk_options = s_dict.get('talk_options', [])
        self.base_convos = s_dict.get('base_convos', {})

        self.action_log = turnwheel.ActionLog.restore(s_dict['action_log'])
        if s_dict.get('records'):
            self.records = records.Recordkeeper.restore(s_dict['records'])
        else:
            self.records = records.Recordkeeper()

        if 'current_random_state' in s_dict:
            static_random.set_combat_random_state(s_dict['current_random_state'])

        if s_dict['level']:
            logger.info("Loading Level...")
            self.current_level = LevelObject.restore(s_dict['level'], self)
            self.set_up_game_board(self.current_level.tilemap)           

            self.generic()

            # Now have units actually arrive on map
            for unit in self.units:
                if unit.position:
                    self.arrive(unit)

            self.cursor.autocursor()

        self.events = event_manager.EventManager.restore(s_dict.get('events'))

    def clean_up(self):
        from app.engine import item_system, skill_system, item_funcs, action

        for unit in self.unit_registry.values():
            self.leave(unit)
        for unit in self.unit_registry.values():
            # Unit cleanup
            if unit.traveler:
                unit.traveler = None
                action.execute(action.RemoveSkill(unit, 'Rescue'))
            unit.set_hp(1000)  # Set to full health
            unit.set_mana(1000)  # Set to full mana
            unit.position = None
            unit.sprite.change_state('normal')
            unit.reset()
        
        for item in self.item_registry.values():
            unit = None
            if item.owner_nid:
                unit = self.get_unit(item.owner_nid)
            item_system.on_end_chapter(unit, item)

        for skill in self.skill_registry.values():
            unit = None
            if skill.owner_nid:
                unit = self.get_unit(skill.owner_nid)
            skill_system.on_end_chapter(unit, skill)

        self.terrain_status_registry.clear()

        # Remove all generics
        self.unit_registry = {k: v for (k, v) in self.unit_registry.items() if not v.generic}

        # Remove any skill that's not on a unit
        for k, v in list(self.skill_registry.items()):
            if v.owner_nid:  # Remove skills from units that no longer exist
                if v.owner_nid not in self.unit_registry:
                    del self.skill_registry[k]
            else:
                del self.skill_registry[k]

        # Remove any item that's not on a unit or in the convoy
        for k, v in list(self.item_registry.items()):
            if v.owner_nid:  # Remove items from units that no longer exist
                if v.owner_nid not in self.unit_registry:
                    del self.item_registry[k]
            else:
                for party in self.parties.values():
                    if v in party.convoy:
                        break
                else:  # No party ever found
                    del self.item_registry[k]

        # Handle player death
        for unit in self.unit_registry.values():
            if unit.dead:
                if not DB.constants.value('permadeath'):
                    unit.dead = False  # Resurrect unit
                elif DB.constants.value('convoy_on_death'):
                    for item in item_funcs.get_all_tradeable_items(unit):
                        unit.remove_item(item)
                        # Put the item in the unit's party's convoy
                        self.parties[unit.party].convoy.append(item)

        # Remove unnecessary information between levels
        self.sweep()
        self.current_level = None

    @property
    def level(self):
        return self.current_level

    @property
    def tilemap(self):
        if self.current_level:
            return self.current_level.tilemap

    @property
    def party(self):
        return self.parties[self.current_party]

    @property
    def units(self):
        return list(self.unit_registry.values())

    def get_units_in_party(self, party=None):
        if party is None:
            party = self.current_party
        return [unit for unit in self.unit_registry.values() if unit.team == 'player' and not unit.dead and not unit.generic and unit.party == party]

    def get_all_units_in_party(self, party=None):
        if party is None:
            party = self.current_party
        return [unit for unit in self.unit_registry.values() if unit.team == 'player' and not unit.generic and unit.party == party]

    def register_unit(self, unit):
        logger.debug("Registering unit %s as %s", unit, unit.nid)
        self.unit_registry[unit.nid] = unit

    def register_item(self, item):
        logger.debug("Registering item %s as %s", item, item.uid)
        self.item_registry[item.uid] = item
        # For multi-items
        for subitem in item.subitems:
            self.item_registry[subitem.uid] = subitem

    def register_skill(self, skill):
        logger.debug("Registering skill %s as %s", skill, skill.uid)
        self.skill_registry[skill.uid] = skill
        # For aura skills
        if skill.subskill:
            self.skill_registry[skill.subskill.uid] = skill.subskill

    def register_terrain_status(self, key, skill_uid):
        logger.debug("Registering terrain status %s", skill_uid)
        self.terrain_status_registry[key] = skill_uid

    def get_unit(self, unit_nid):
        """
        Can get units not just in the current level
        Could be used to get units in overworld, base,
        etc.
        """
        unit = self.unit_registry.get(unit_nid)
        return unit

    def get_item(self, item_uid):
        item = self.item_registry.get(item_uid)
        return item

    def get_skill(self, skill_uid):
        skill = self.skill_registry.get(skill_uid)
        return skill

    def get_terrain_status(self, key):
        skill_uid = self.terrain_status_registry.get(key)
        return skill_uid

    def get_party(self, party_nid):
        return self.parties.get(party_nid)

    def get_player_units(self):
        return [unit for unit in self.unit_registry.values() if unit.team == 'player' and unit.position and not unit.dead and not unit.is_dying and 'Tile' not in unit.tags]

    def get_enemy_units(self):
        return [unit for unit in self.unit_registry.values() if unit.team.startswith('enemy') and unit.position and not unit.dead and not unit.is_dying and 'Tile' not in unit.tags]

    def check_dead(self, nid):
        unit = self.get_unit(nid)
        if unit and (unit.dead or unit.is_dying):
            return True
        return False

    def check_alive(self, nid):
        unit = self.get_unit(nid)
        if unit and not (unit.dead or unit.is_dying):
            return True
        return False

    def leave(self, unit, test=False):
        """
        # Removes a unit from the map
        # This function should always be called BEFORE changing the unit's position
        # Handles:
        # 1. removing the unit from the boundary manager
        # 2. Removes any auras from the unit's skill list, since they will no longer be on the map
        # 3. Removes any of the unit's own auras from the map
        # 4. Removes any status/skills that the terrain or regions on the map are giving 
        # the unit
        #
        # If "test" is True, some of these are skipped, such as removing the unit from
        # the boundary manager and registering these actions with the action_log
        # Set "test" to True when you are just testing what would happen by moving 
        # to a position (generally used for AI)
        """
        from app.engine import action, aura_funcs
        if unit.position:
            logger.debug("Leave %s %s", unit.nid, unit.position)
            # Boundary
            if not test:
                self.boundary.leave(unit)
            # Auras
            for aura_data in game.board.get_auras(unit.position):
                child_aura_uid, target = aura_data
                child_skill = self.get_skill(child_aura_uid)
                aura_funcs.remove_aura(unit, child_skill, test)
            if not test:
                for skill in unit.skills:
                    if skill.aura:
                        aura_funcs.release_aura(unit, skill, self)
            # Regions
            for region in game.level.regions:
                if region.region_type == 'status' and region.contains(unit.position):
                    act = action.RemoveSkill(unit, region.sub_nid)
                    if test:
                        act.do()
                    else:
                        action.do(act)
            # Tiles
            terrain_nid = self.tilemap.get_terrain(unit.position)
            terrain = DB.terrain.get(terrain_nid)
            if terrain.status:
                act = action.RemoveSkill(unit, terrain.status)
                if test:
                    act.do()
                else:
                    action.do(act)
            # Board
            if not test:
                self.board.remove_unit(unit.position, unit)

    def arrive(self, unit, test=False):
        """
        # Adds a unit to the map
        # This function should always be called AFTER changing the unit's position
        # Handles:
        # 1. adding the unit to the boundary manager
        # 2. adding any auras from that the unit should be affected by to the the unit's skill list
        # 3. Adding any of the unit's own auras to other units
        # 4. Adding any status/skills that the terrain or regions on the map are giving 
        #
        # If "test" is True, some of these are skipped, such as adding the unit to
        # the boundary manager and registering these actions with the action_log
        # Set "test" to True when you are just testing what would happen by moving 
        # to a position (generally used for AI)
        """
        from app.engine import skill_system, aura_funcs
        if unit.position:
            logger.debug("Arrive %s %s", unit.nid, unit.position)
            if not test:
                self.board.set_unit(unit.position, unit)
            # Tiles
            if not skill_system.ignore_terrain(unit):
                self.add_terrain_status(unit, test)
            # Regions
            if not skill_system.ignore_region_status(unit):
                for region in game.level.regions:
                    if region.region_type == 'status' and region.contains(unit.position):
                        self.add_region_status(unit, region, test)
            # Auras
            aura_funcs.pull_auras(unit, self, test)
            if not test:
                for skill in unit.skills:
                    if skill.aura:
                        aura_funcs.propagate_aura(unit, skill, self)
            # Boundary
            if not test:
                self.boundary.arrive(unit)

    def add_terrain_status(self, unit, test):
        from app.engine import action
        layer = self.tilemap.get_layer(unit.position)
        key = (*unit.position, layer)  # Terrain position and layer
        skill_uid = self.get_terrain_status(key)
        # Doesn't bother creating a new skill if the skill already exists in data
        if skill_uid: 
            skill_obj = self.get_skill(skill_uid)
            act = action.AddSkill(unit, skill_obj)
        else:
            act = None
            terrain_nid = self.tilemap.get_terrain(unit.position)
            terrain = DB.terrain.get(terrain_nid)
            if terrain.status:
                act = action.AddSkill(unit, terrain.status)
                self.register_terrain_status(key, act.skill_obj.uid)
        if act:
            if test:
                act.do()
            else:
                action.do(act)

    def add_region_status(self, unit, region, test):
        from app.engine import action
        skill_uid = self.get_terrain_status(region.nid)
        if skill_uid:
            skill_obj = self.get_skill(skill_uid)
            act = action.AddSkill(unit, skill_obj)
        else:
            act = action.AddSkill(unit, region.sub_nid)
            self.register_terrain_status(region.nid, act.skill_obj.uid)
        if test:
            act.do()
        else:
            action.do(act)

    def check_for_region(self, position, region_type, sub_nid=None):
        for region in game.level.regions:
            if region.region_type == region_type and region.contains(position):
                if not sub_nid or region.sub_nid == sub_nid:
                    return region
        return None

    def get_all_formation_spots(self) -> list:
        legal_spots = set()
        for region in game.level.regions:
            if region.region_type == 'formation':
                for x in range(region.size[0]):
                    for y in range(region.size[1]):
                        legal_spots.add((region.position[0] + x, region.position[1] + y))
        return legal_spots

    def get_open_formation_spots(self) -> list:
        all_formation_spots = self.get_all_formation_spots()
        return sorted({pos for pos in all_formation_spots if not self.board.get_unit(pos)})

    def get_next_formation_spot(self) -> tuple:
        legal_spots = self.get_open_formation_spots()
        if legal_spots:
            return legal_spots[0]
        return None

    def get_money(self):
        return self.parties[self.current_party].money

    def set_money(self, val):
        self.parties[self.current_party].money = val

game = GameState()

def start_game():
    global game
    if not game:
        game = GameState()
    else:
        game.clear()  # Need to use old game if called twice in a row
    game.load_states(['title_start'])
    return game

def start_level(level_nid):
    global game
    logging.info("Start Level %s" % level_nid)
    if not game:
        game = GameState()
    else:
        game.clear()  # Need to use old game if called twice in a row
    game.load_states(['turn_change'])
    game.build_new()
    game.start_level(level_nid)
    return game

def load_level(level_nid, save_loc):
    global game
    logging.info("Load Level %s" % level_nid)
    if not game:
        game = GameState()
    else:
        game.clear()
    import pickle
    from app.engine import save
    with open(save_loc, 'rb') as fp:
        s_dict = pickle.load(fp)
    game.load_states(['turn_change'])
    game.build_new()
    game.load(s_dict)
    save.set_next_uids(game)
    game.start_level(level_nid)
    return game
