from collections import Counter

from app.engine import input_manager, state_machine

import logging
logger = logging.getLogger(__name__)

class GameState():
    def __init__(self):
        self.game_constants = Counter()
        self.memory = {}

        self.input_manager = input_manager.InputManager()
        self.state = state_machine.StateMachine()

        self.playtime = 0

    def load_states(self, starting_states):
        self.state.load_states(starting_states)

game = None

def start_game():
    global game
    game = GameState()
    game.load_states(['title_start'])
    return game
