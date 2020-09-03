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
        self.game_constants = Counter()
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
        self.game_constants.clear()

        # Set up random seed
        if cf.SETTINGS['random_seed'] >= 0:
            random_seed = int(cf.SETTINGS['random_seed'])
        else:
            random_seed = random.randint(0, 1023)
        static_random.set_seed(random_seed)
        self.game_constants['_random_seed'] = random_seed

        # Set up overworld  TODO
        if DB.constants.value('overworld'):
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
        from app.engine import cursor, camera, phase, highlight, \
            movement, death, ai_controller
        # Systems
        self.cursor = cursor.Cursor()
        self.camera = camera.Camera()
        self.phase = phase.PhaseController()
        self.highlight = highlight.HighlightController()
        self.moving_units = movement.MovementManager()
        self.death = death.DeathManager()
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
                  'game_constants': self.game_constants,
                  'level_constants': self.level_constants,
                  'parties': [party.save() for party in self.parties.values()],
                  'current_party': self.current_party,
                  'state': self.state.save(),
                  'action_log': self.action_log.save()
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
        self.game_constants = Counter(s_dict.get('game_constants', {}))
        self.level_constants = Counter(s_dict.get('level_constants', {}))
        self.playtime = float(s_dict['playtime'])
        self.parties = {nid: PartyObject.restore(party) for nid, party in s_dict['parties'].items()}
        self.current_party = s_dict['current_party']
        self.turncount = int(s_dict['turncount'])

        self.state.load_states(s_dict['state'][0], s_dict['state'][1])

        self.item_registry = {item['uid']: ItemObject.restore(item) for item in s_dict['items']}
        self.status_registry = {skill['uid']: SkillObject.restore(skill) for skill in s_dict['skill']}
        self.unit_registry = {unit['nid']: UnitObject.restore(unit) for unit in s_dict['units']}

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
        from app.engine import item_system

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
                    for item in unit.items:
                        if not item.locked:
                            unit.remove_item(item)
                            # Put the item in the unit's party's convoy
                            self.parties[unit.party].convoy.append(item)

        # Remove unnecessary information between levels
        self.sweep()
        self.current_level = None

    @property
    def level(self):
        return self.current_level

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

    # For placing units on map and removing them from map
    def leave(self, unit, test=False):
        if unit.position:
            logger.info("Leave %s %s", unit.nid, unit.position)
            if not test:
                game.board.set_unit(unit.position, None)
                game.boundary.leave(unit)
            # Tiles
        # Auras

    def arrive(self, unit, test=False):
        if unit.position:
            logger.info("Arrive %s %s", unit.nid, unit.position)
            if not test:
                game.board.set_unit(unit.position, unit)
                game.boundary.arrive(unit)
            # Tiles
            # Auras

game = None

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
