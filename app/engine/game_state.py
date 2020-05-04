import random
from collections import Counter

from app.data.constants import VERSION
from app.data.party import Party
from app.data.items import Item
from app.data.database import DB

from app.engine import state_machine, input_manager, static_random, a_star, equations
from app.engine import config as cf

import logging
logger = logging.getLogger(__name__)

# TODO
class Status():
    pass

class GameState():
    def __init__(self):
        self.game_constants = Counter()
        self.memory = {}

        self.input_manager = input_manager.InputManager()
        self.equations = equations.Parser(self)
        self.state = state_machine.StateMachine()

        self.playtime = 0

    def load_states(self, starting_states):
        self.state.load_states(starting_states)

    # Start a new game
    def build_new(self):
        logger.info("Building New Game")
        self.playtime = 0

        self.parties = {}
        self.current_party = None
        self.current_level = None
        self.tilemap = None
        self.game_constants.clear()

        # Set up random seed
        if cf.SETTINGS['random_seed'] >= 0:
            random_seed = int(cf.SETTINGS['random_seed'])
        else:
            random_seed = random.randint(0, 1023)
        static_random.set_seed(random_seed)
        self.game_constants['_random_seed'] = random_seed

        # Set up overworld  TODO
        if DB.constants.get('overworld').value:
            self.overworld = None
        else:
            self.overworld = None

        self.records = []
        self.sweep()
        self.generic()

    def sweep(self):
        """
        Cleans up variables that need to be reset at the end of each level
        """
        from app.engine import turnwheel
        self.unit_registry = {}
        self.item_registry = {}
        self.status_registry = {}
        self.level_constants = Counter()
        self.turncount = 0
        self.action_log = turnwheel.ActionLog()

    def generic(self):
        """
        Done on loading a level, whether from overworld, last level, save_state, etc.
        """
        from app.engine import cursor, camera, phase, highlight, targets, \
            movement, death, ai_controller
        self.cursor = cursor.Cursor()
        self.camera = camera.Camera()
        self.phase = phase.PhaseController()
        self.highlight = highlight.HighlightController()
        self.targets = targets.TargetSystem()
        self.moving_units = movement.MovementManager()
        self.death = death.DeathManager()
        self.combat_instance = None
        self.ai = ai_controller.AIController()

        self.alerts = []

        # Build registries
        self.map_sprite_registry = {}

    def start_level(self, level_nid):
        """
        Done at the beginning of a new level to start the level up
        """
        from app.data.level_object import LevelObject
        level_prefab = DB.levels.get(level_nid)
        serialized_tilemap = level_prefab.tilemap.serialize()
        self.tilemap = self.load_map(serialized_tilemap)
        self.current_level = LevelObject.from_prefab(level_prefab, self.tilemap)

        for unit in self.current_level.units:
            self.register_unit(unit)
            for item in unit.items:
                self.register_item(item)
        for unit in self.current_level.units:
            self.arrive(unit)

    def load_map(self, serialized_tilemap):
        from app.engine import map_view, ui_view, boundary
        from app.data.tilemap import TileMap
        tilemap = TileMap.deserialize(serialized_tilemap)  # To make a copy
        self.grid = a_star.GridManager(tilemap)
        self.boundary = boundary.BoundaryInterface(tilemap.width, tilemap.height)
        self.map_view = map_view.MapView(tilemap)
        self.ui_view = ui_view.UIView()
        return tilemap

    def save(self):
        self.action_log.record = False
        s_dict = {'units': [unit.serialize() for unit in self.unit_registry.values()],
                  'items': [item.serialize() for item in self.item_registry.values()],
                  'status': [status.serialize() for status in self.status_registry.values()],
                  'level': self.current_level.serialize(),
                  'turncount': self.turncount,
                  'playtime': self.playtime,
                  'game_constants': self.game_constants,
                  'level_constants': self.level_constants,
                  'parties': {nid: party.serialize() for nid, party in self.parties.values()},
                  'current_party': self.current_party,
                  'state': self.state.serialize(),
                  'action_log': self.action_log.serialize()
                  }
        import time
        meta_dict = {'playtime': self.playtime,
                     'realtime': time.time(),
                     'version': VERSION,
                     'title': DB.constants.get('title').value,
                     'level_title': self.current_level.title,
                     }
        self.action_log.record = True
        return s_dict, meta_dict

    def load(self, s_dict):
        from app.engine import turnwheel
        from app.data.unit_object import UnitObject
        from app.data.level_object import LevelObject

        logger.info("Loading Game...")
        self.game_constants = Counter(s_dict.get('game_constants', {}))
        self.level_constants = Counter(s_dict.get('level_constants', {}))
        self.playtime = float(s_dict['playtime'])
        self.parties = {nid: Party.deserialize(party) for nid, party in s_dict['parties'].items()}
        self.current_party = s_dict['current_party']
        self.turncount = int(s_dict['turncount'])

        self.state.load_states(s_dict['state'][0], s_dict['state'][1])

        self.item_registry = {item['uid']: Item.deserialize(item, DB.items.get_instance(item['nid'])) for item in s_dict['items']}
        self.status_registry = {status['uid']: Status.deserialize(status, DB.status.get(status['nid'])) for status in s_dict['status']}
        self.unit_registry = {unit['nid']: UnitObject.deserialize(unit) for unit in s_dict['units']}

        self.action_log = turnwheel.ActionLog.deserialize(s_dict['action_log'])

        logger.info("Loading Map...")
        self.tilemap = self.load_map(s_dict['level']['tilemap'])
        self.current_level = LevelObject.deserialize(s_dict['level'], self.tilemap, self)

        self.generic()

        # Now have units actually arrive on map
        for unit in self.current_level.units:
            self.arrive(unit)

    @property
    def level(self):
        return self.current_level

    def register_unit(self, unit):
        logger.info("Registering unit %s as %s", unit, unit.nid)
        self.unit_registry[unit.nid] = unit

    def register_item(self, item):
        logger.info("Registering item %s as %s", item, item.uid)
        self.item_registry[item.uid] = item

    def register_status(self, status):
        logger.info("Registering status %s as %s", status, status.uid)
        self.item_registry[status.uid] = status

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

    def get_status(self, status_uid):
        status = self.item_registry.get(status_uid)
        return status

    # For placing units on map and removing them from map
    def leave(self, unit, test=False):
        if unit.position:
            logger.info("Leave %s %s", unit.nid, unit.position)
            if not test:
                game.grid.set_unit(unit.position, None)
                game.boundary.leave(unit)
            # Tiles
        # Auras

    def arrive(self, unit, test=False):
        if unit.position:
            logger.info("Arrive %s %s", unit.nid, unit.position)
            if not test:
                game.grid.set_unit(unit.position, unit)
                game.boundary.arrive(unit)
            # Tiles
            # Auras

game = None

def start_game():
    global game
    game = GameState()
    game.load_states(['title_start'])
    return game

def start_level(level_nid):
    global game
    game = GameState()
    game.load_states(['turn_change'])
    game.build_new()
    game.start_level(level_nid)
    return game
