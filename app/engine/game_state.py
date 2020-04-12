import random
from collections import Counter

from app.engine import state_machine, static_random, a_star
from app.engine import config as cf

from app.data.database import DB

import logging
logger = logging.getLogger(__name__)

class GameState():
    def __init__(self):
        self.game_constants = Counter()
        self.memory = {}

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
        self.level_constants = Counter()
        self.turncount = 0
        # self.action_log = turnwheel.ActionLog()

    def generic(self):
        """
        Done on loading a level, whether from overworld, last level, save_state, etc.
        """
        from app.engine import cursor
        self.cursor = cursor.Cursor()

    def start_level(self, level_nid):
        """
        Done at the beginning of a new level to start the level up
        """
        self.current_level = DB.levels.get(level_nid)
        self.tilemap = self.load_map(self.current_level.tilemap)

    def load_map(self, tilemap):
        # TODO
        from app.engine.map_view import MapView
        self.grid = a_star.GridManager(tilemap)
        # self.boundary = boundary.BoundaryInterface(tilemap)
        self.map_view = MapView(tilemap)
        return tilemap

    @property
    def level(self):
        return self.current_level

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
