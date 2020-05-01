import random
from collections import Counter

from app.data.database import DB

from app.engine import state_machine, input_manager, static_random, a_star, equations
from app.engine import config as cf

import logging
logger = logging.getLogger(__name__)

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
        self.item_registry = {}
        self.map_sprite_registry = {}

    def start_level(self, level_nid):
        """
        Done at the beginning of a new level to start the level up
        """
        from app.data.level_object import LevelObject
        from app.engine import boundary
        level_prefab = DB.levels.get(level_nid)
        self.tilemap = self.load_map(level_prefab.tilemap)
        self.current_level = LevelObject(level_prefab, self.tilemap)

        self.boundary = boundary.BoundaryInterface(self.tilemap.width, self.tilemap.height)

        for unit in self.current_level.units:
            for item in unit.items:
                self.register_item(item)
        for unit in self.current_level.units:
            self.arrive(unit)

    def load_map(self, tilemap):
        from app.data.tilemap import TileMap
        from app.engine import map_view
        s = tilemap.serialize()
        tilemap = TileMap.deserialize(s)  # To make a copy
        self.grid = a_star.GridManager(tilemap)
        # self.boundary = boundary.BoundaryInterface(tilemap)
        self.map_view = map_view.MapView(tilemap)
        return tilemap

    @property
    def level(self):
        return self.current_level

    def register_item(self, item):
        logger.info("Registering item %s as %s", item, item.uid)
        self.item_registry[item.uid] = item

    def get_unit(self, unit_nid):
        """
        Can get units not just in the current level
        Could be used to get units in overworld, base,
        etc.
        """
        unit = self.level.units.get(unit_nid)
        if unit:
            return unit
        for party in self.parties:
            unit = party.units.get(unit_nid)
            if unit:
                return unit

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
