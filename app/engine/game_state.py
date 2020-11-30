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

    def load_states(self, starting_states):
        self.state.load_states(starting_states)

    # Start a new game
    # When the player clicks "New Game"
    def build_new(self):
        logger.info("Building New Game")
        self.playtime = 0

        self.unit_registry = {}
        self.item_registry = {}
        self.skill_registry = {}

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

        self.records = []
        self.market_items = []
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
        self.moving_units = movement.MovementManager()
        self.death = death.DeathManager()
        self.ui_view = ui_view.UIView()
        self.combat_instance = None
        self.ai = ai_controller.AIController()

        self.alerts.clear()

        # Build registries
        self.map_sprite_registry = {}

    def start_level(self, level_nid):
        """
        Done at the beginning of a new level to start the level up
        """
        self.generic()
        
        from app.engine.objects.level import LevelObject
        from app.engine.objects.tilemap import TileMapObject

        level_prefab = DB.levels.get(level_nid)
        tilemap_nid = level_prefab.tilemap
        tilemap_prefab = RESOURCES.tilemaps.get(tilemap_nid)
        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        self.current_level = LevelObject.from_prefab(level_prefab, tilemap)
        # Assign every unit the levels party if they don't already have one
        for unit in self.current_level.units:
            if not unit.party:
                unit.party = self.current_level.party
        self.set_up_game_board(self.current_level.tilemap)

        for unit in self.current_level.units:
            self.register_unit(unit)
            for item in unit.items:
                self.register_item(item)
        for unit in self.current_level.units:
            self.arrive(unit)

    def set_up_game_board(self, tilemap):
        from app.engine import game_board, boundary
        self.board = game_board.GameBoard(tilemap)
        self.boundary = boundary.BoundaryInterface(tilemap.width, tilemap.height)

    def save(self):
        self.action_log.record = False
        s_dict = {'units': [unit.save() for unit in self.unit_registry.values()],
                  'items': [item.save() for item in self.item_registry.values()],
                  'skills': [skill.save() for skill in self.skill_registry.values()],
                  'level': self.current_level.save() if self.current_level else None,
                  'turncount': self.turncount,
                  'playtime': self.playtime,
                  'game_vars': self.game_vars,
                  'level_vars': self.level_vars,
                  'parties': [party.save() for party in self.parties.values()],
                  'current_party': self.current_party,
                  'state': self.state.save(),
                  'action_log': self.action_log.save(),
                  'market_items': self.market_items,  # Item nids
                  'talk_options': self.talk_options,
                  'already_triggered_events': self.already_triggered_events,
                  }
        meta_dict = {'playtime': self.playtime,
                     'realtime': time.time(),
                     'version': VERSION,
                     'title': DB.constants.value('title'),
                     'level_title': self.current_level.name,
                     }
        self.action_log.record = True
        return s_dict, meta_dict

    def load(self, s_dict):
        from app.engine import turnwheel

        from app.engine.objects.item import ItemObject
        from app.engine.objects.skill import SkillObject
        from app.engine.objects.unit import UnitObject
        from app.engine.objects.level import LevelObject
        from app.engine.objects.party import PartyObject

        logger.info("Loading Game...")
        self.game_vars = Counter(s_dict.get('game_vars', {}))
        self.level_vars = Counter(s_dict.get('level_vars', {}))
        self.playtime = float(s_dict['playtime'])
        self.parties = {party_data['nid']: PartyObject.restore(party_data) for party_data in s_dict['parties']}
        self.current_party = s_dict['current_party']
        self.turncount = int(s_dict['turncount'])

        self.state.load_states(s_dict['state'][0], s_dict['state'][1])

        self.item_registry = {item['uid']: ItemObject.restore(item) for item in s_dict['items']}
        self.skill_registry = {skill['uid']: SkillObject.restore(skill) for skill in s_dict['skills']}
        self.unit_registry = {unit['nid']: UnitObject.restore(unit) for unit in s_dict['units']}

        self.market_items = s_dict.get('market_items', [])
        self.already_triggered_events = s_dict.get('already_triggered_events', [])
        self.talk_options = s_dict.get('talk_options', [])

        self.action_log = turnwheel.ActionLog.restore(s_dict['action_log'])

        if s_dict['level']:
            logger.info("Loading Level...")
            self.current_level = LevelObject.restore(s_dict['level'], self)
            self.set_up_game_board(self.current_level.tilemap)            

            self.generic()

            # Now have units actually arrive on map
            for unit in self.current_level.units:
                self.arrive(unit)

    def clean_up(self):
        from app.engine import item_system, item_funcs

        for unit in self.unit_registry.values():
            self.leave(unit)
        for unit in self.unit_registry.values():
            unit.clean_up()
        
        for item in self.item_registry.values():
            unit = None
            if item.owner_nid:
                unit = self.get_unit(item.owner_nid)
            item_system.on_end_chapter(unit, item)

        # Remove non-player team units and all generics
        self.unit_registry = {k: v for (k, v) in self.unit_registry.items() if v.team == 'player' and not v.generic}

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
        return self.current_level.tilemap

    @property
    def party(self):
        return self.parties[self.current_party]

    def get_units_in_party(self, party=None):
        if party is None:
            party = self.current_party
        return [unit for unit in self.unit_registry.items() if unit.team == 'player' and not unit.dead and not unit.generic and unit.party == party]

    def register_unit(self, unit):
        logger.info("Registering unit %s as %s", unit, unit.nid)
        self.unit_registry[unit.nid] = unit

    def register_item(self, item):
        logger.info("Registering item %s as %s", item, item.uid)
        self.item_registry[item.uid] = item

    def register_skill(self, skill):
        logger.info("Registering skill %s as %s", skill, skill.uid)
        self.skill_registry[skill.uid] = skill

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
        skill = self.item_registry.get(skill_uid)
        return skill

    def get_party(self, party_nid):
        return self.parties.get(party_nid)

    def get_player_units(self):
        return [unit for unit in self.level.units if unit.team == 'player' and unit.position and not unit.dead and not unit.is_dying]

    def get_enemy_units(self):
        return [unit for unit in self.level.units if unit.team.startswith('enemy') and unit.position and not unit.dead and not unit.is_dying]

    def check_dead(self, nid):
        return any(unit.nid == nid and (unit.dead or unit.is_dying) for unit in game.level.units)

    def check_alive(self, nid):
        return any(unit.nid == nid and not (unit.dead or unit.is_dying) for unit in game.level.units)

    # For placing units on map and removing them from map
    def leave(self, unit, test=False):
        from app.engine import action
        if unit.position:
            logger.info("Leave %s %s", unit.nid, unit.position)
            if not test:
                self.board.set_unit(unit.position, None)
                self.boundary.leave(unit)
            # Tiles
            terrain_nid = self.tilemap.get_terrain(unit.position)
            terrain = DB.terrain.get(terrain_nid)
            if terrain.status:
                action.do(action.RemoveSkill(unit, terrain.status))
        # Auras

    def arrive(self, unit, test=False):
        from app.engine import skill_system, action
        if unit.position:
            logger.info("Arrive %s %s", unit.nid, unit.position)
            if not test:
                self.board.set_unit(unit.position, unit)
                self.boundary.arrive(unit)
            # Tiles
            if not skill_system.ignore_terrain(unit):
                terrain_nid = self.tilemap.get_terrain(unit.position)
                terrain = DB.terrain.get(terrain_nid)
                if terrain.status:
                    new_skill = DB.skills.get(terrain.status)
                    action.do(action.AddSkill(unit, new_skill))
            # Auras

    def check_for_region(self, position, region_type):
        raise NotImplementedError

    def get_all_formation_spots(self) -> list:
        legal_spots = set()
        for region in game.level.regions:
            if region.region_type == 'Formation':
                for x in range(region.size[0]):
                    for y in range(region.size[1]):
                        legal_spots.add((region.position[0] + x, region.position[1] + y))
        return legal_spots

    def get_next_formation_spot(self) -> tuple:
        legal_spots = sorted(self.get_all_formation_spots())
        if legal_spots:
            return legal_spots[0]
        return None

    def get_money(self):
        return self.party.money

    def set_money(self, val):
        self.party.money = val

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
    print("Start Level %s" % level_nid)
    if not game:
        game = GameState()
    else:
        game.clear()  # Need to use old game if called twice in a row
    game.load_states(['turn_change'])
    game.build_new()
    game.start_level(level_nid)
    return game
