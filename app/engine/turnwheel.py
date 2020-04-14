from dataclasses import dataclass
from app.engine.game_state import game
import app.engine.action as Action

import logging
logger = logging.getLogger(__name__)

class ActionLog():
    def __init__(self):
        self.actions = []
        self.action_index = -1  # Means no actions
        self.first_free_action = -1
        self.locked = False
        self.record = True  # Whether the action log is currently recording
        self.action_depth = 0

        # For playback
        self.current_unit = None
        self.hovered_unit = None
        self.current_move = None
        self.current_move_index = 0
        self.unique_moves = []

    def append(self, action):
        logger.info("Add Action %d: %s", self.action_index + 1, action.__class__.__name__)
        self.actions.append(action)
        self.action_index += 1

    def remove(self, action):
        logger.info("Remove Action %d: %s", self.action_index, action.__class__.__name__)
        self.actions.remove(action)
        self.action_index -= 1

    def run_action_backward(self):
        action = self.actions[self.action_index]
        action.reverse()
        self.action_index -= 1
        return action

    def run_action_forward(self):
        self.action_index += 1
        action = self.actions[self.action_index]
        action.execute()
        return action

    def at_far_past(self):
        return not self.actions or self.action_index <= self.first_free_action

    def at_far_future(self):
        return not self.actions or self.action_index + 1 >= len(self.actions)

    @dataclass
    class Move():
        unit: str = None
        begin: int = None
        end: int = None

        def __repr__(self):
            return "Move: %s (%s %s)" % (self.unit.nid, self.begin, self.end)

    def set_up(self):
        def finalize(move):
            if isinstance(move, self.Move) and move.end is None:
                move.end = move.begin
            self.unique_moves.append(move)
        
        # Pay attention to which actions the turnwheel actually has to know about
        self.unique_moves.clear()
        current_move = None

        for action_index in range(self.first_free_action, len(self.actions)):
            action = self.actions[action_index]
            # Only regular moves, not CantoMove or other nonsense gets counted
            if type(action) == Action.Move or type(action) == Action.Teleport:
                if current_move:
                    finalize(current_move)
                current_move = self.Move(action.unit, action_index)
            elif isinstance(action, Action.Wait) or isinstance(action, Action.Die):
                if current_move and action.unit == current_move.unit:
                    current_move.end = action_index
                    finalize(current_move)
                    current_move = None
            elif isinstance(action, Action.MarkPhase):
                if current_move:
                    finalize(current_move)
                    current_move = None
                self.unique_moves.append(('Phase', action_index, action.phase_name))
            elif isinstance(action, Action.LockTurnwheel):
                if current_move:
                    finalize(current_move)
                    current_move = None
                self.unique_moves(('Lock', action_index, action.lock))

        # Handles having extra actions off the right of the action log
        if self.unique_moves:
            last_move = self.unique_moves[-1]
            last_action_index = len(self.actions) - 1
            if isinstance(last_move, self.Move):
                if last_move.end < last_action_index:
                    self.unique_moves.append(('Extra', last_move.end + 1, last_action_index ))
            elif last_move[1] < last_action_index:
                self.unique_moves.append(('Extra', last_move[1] + 1, last_action_index))

        logger.info("*** Turnwheel Begin ***")
        logger.info(self.unique_moves)

        self.current_move_index = len(self.unique_moves)

        # Determine starting lock
        self.locked = self.get_last_lock()

        # Get the text message
        for move in reversed(self.unique_moves):
            if isinstance(move, self.Move):
                if move.end:
                    text_list = self.get_unit_turn(move.unit, move.end)
                    return text_list
                return []
            elif move[0] == 'Phase':
                return ["Start of %s phase" % move[2].capitalize()]
        return []

    def backward(self):
        if self.current_move_index < 1:
            return None

        self.current_move = self.unique_moves[self.current_move_index - 1]
        logger.info("Backward %s %s %s", self.current_move_index, self.current_move, self.action_index)
        self.current_move_index -= 1
        action = None

        if isinstance(self.current_move, self.Move):
            if self.current_unit:
                while self.action_index >= self.current_move.begin:
                    action = self.run_action_backward()
                game.cursor.set_pos(self.current_unit.position)
                self.current_unit = None
                return []
            else:
                if self.hovered_unit:
                    self.hover_off()
                self.current_unit = self.current_move.unit
                if self.current_move.end:
                    while self.action_index > self.current_move.end:
                        action = self.run_action_backward()
                    prev_action = None
                    if self.action_index >= 1:
                        prev_action = self.actions[self.action_index]
                        logger.info("Prev Action %s", prev_action)
                    if self.current_unit.position:
                        game.cursor.set_pos(self.current_unit.position)
                    # Unless the current unit just DIED!
                    elif isinstance(prev_action, Action.Die):
                        game.cursor.set_pos(prev_action.old_pos)
                    self.hover_on(self.current_unit)
                    text_list = self.get_unit_turn(self.current_unit, self.action_index)
                    self.current_move_index += 1
                    logger.info("In Backward %s %s %s %s", text_list, self.current_unit.nid, self.current_unit.position, prev_action)
                    return text_list
                else:
                    while self.action_index >= self.current_move.begin:
                        action = self.run_action_backward()
                    game.cursor.set_pos(self.current_unit.position)
                    self.hover_on(self.current_unit)
                    return []

        elif self.current_move[0] == 'Phase':
            while self.action_index > self.current_move[1]:
                action = self.run_action_backward()
            if self.hovered_unit:
                self.hover_off()
            if self.current_move[2] == 'player':
                game.cursor.autocursor()
            return ["Start of %s phase" % self.current_move[2].capitalize()]

        elif self.current_move[0] == 'Lock':
            while self.action_index >= self.current_move[1]:
                action = self.run_action_backward()
            self.locked = self.get_last_lock()
            return self.backward()  # Go again

        elif self.current_move[0] == 'Extra':
            while self.action_index >= self.current_move[1]:
                action = self.run_action_backward()
            return self.backward()  # Go again

    def forward(self):
        if self.current_move_index >= len(self.unique_moves):
            return None

        self.current_move = self.unique_moves[self.current_move_index]
        logger.info("Forward %s %s %s", self.current_move_index, self.current_move, self.action_index)
        self.current_move_index += 1
        action = None

        if isinstance(self.current_move, self.Move):
            if self.current_unit:
                while self.action_index < self.current_move.end:
                    action = self.run_action_forward()
                if self.current_unit.position:
                    game.cursor.set_pos(self.current_unit.position)
                elif isinstance(action, Action.Die):
                    game.cursor.set_pos(action.old_pos)
                text_list = self.get_unit_turn(self.current_unit, self.action_index)
                logger.info("In Forward %s %s %s", text_list, self.current_unit.name, action)
                self.current_unit = None
                # Extra Moves
                if self.current_move_index < len(self.unique_moves):
                    next_move = self.unique_moves[self.current_move_index]
                    if isinstance(next_move, tuple) and next_move[0] == 'Extra':
                        self.forward()  # Skip through the extra move
                return text_list
            else:  # Get the next hovered unit
                if self.hovered_unit:
                    self.hover_off()
                self.current_unit = self.current_move.unit
                while self.action_index < self.current_move.begin - 1:
                    # Does next action, so -1 is necessary
                    action = self.run_action_forward()
                game.cursor.set_pos(self.current_unit.position)
                self.hover_on(self.current_unit)
                self.current_move_index -= 1  # Make sure we don't skip second half of this
                return []

        elif self.current_move[0] == 'Phase':
            while self.action_index < self.current_move[1]:
                action = self.run_action_forward()
            if self.hovered_unit:
                self.hover_off()
            if self.current_move[2] == 'player':
                game.cursor.autocursor()
            return ["Start of %s phase" % self.current_move[2].capitalize()]

        elif self.current_move[0] == 'Lock':
            while self.action_index < self.current_move[1]:
                action = self.run_action_forward()
            self.locked = self.current_move[2]
            return self.forward()  # Go again

        elif self.current_move[0] == 'Extra':
            while self.action_index < self.current_move[1]:
                action = self.run_action_forward()
            return []

    def finalize(self):
        """
        Removes all actions after the one we turned back to
        """
        self.current_unit = None
        if self.hovered_unit:
            self.hover_off()
        self.actions = self.actions[:self.action_index + 1]

    def reset(self):
        """
        Pretend we never touched turnwheel
        """
        self.current_unit = None
        if self.hovered_unit:
            self.hover_off()
        while not self.at_far_future():
            self.run_action_forward()

    def get_last_lock(self):
        cur_index = self.action_index
        while cur_index > self.first_free_action:
            cur_index -= 1
            cur_action = self.actions[cur_index]
            if isinstance(cur_action, Action.LockTurnwheel):
                return cur_action.lock
        return False  # Assume not locked

    def get_current_phase(self):
        cur_index = self.action_index
        while cur_index > 0:
            cur_index -= 1
            cur_action = self.actions[cur_index]
            if isinstance(cur_action, Action.MarkPhase):
                return cur_action.phase_name
        return 'player'

    def is_turned_back(self):
        return self.action_index + 1 < len(self.actions)

    def can_use(self):
        return self.is_turned_back() and not self.locked

    def get_unit_turn(self, unit, wait_index):
        cur_index = wait_index
        text = []
        while cur_index > self.first_free_action:
            cur_index -= 1
            cur_action = self.actions[cur_index]
            if isinstance(cur_action, Action.Message):
                text.insert(0, cur_action.message)
            elif isinstance(cur_action, Action.Move):
                return text

    def get_previous_position(self, unit):
        for action in reversed(self.actions):
            if isinstance(action, Action.Move):
                if action.unit == unit:
                    return action.old_pos
        return unit.position

    def set_first_free_action(self):
        if self.first_free_action == -1:
            logger.info("*** First Free Action ***")
            self.first_free_action = self.action_index

    def hover_on(self, unit):
        game.cursor.set_turnwheel_sprite()
        self.hovered_unit = unit

    def hover_off(self):
        game.cursor.hide()
        self.hovered_unit = None

    def serialize(self):
        return ([action.serialize() for action in self.actions], self.first_free_action)

    @classmethod
    def deserializee(cls, serial):
        self = cls()
        actions, first_free_action = serial
        for name, action in actions:
            self.append(getattr(Action, name).deserialize(action))
        self.first_free_action = first_free_action
        return self
