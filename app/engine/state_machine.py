import logging
logger = logging.getLogger(__name__)

class StateMachine():
    def __init__(self):
        self.state = []
        self.temp_state = []

    def load_states(self, starting_states=None):
        from app.engine import title_screen, transitions, general_states
        self.all_states = {'title_start': title_screen.TitleStartState,
                           'transition_in': transitions.TransitionInState,
                           'turn_change': general_states.TurnChangeState,
                           'free': general_states.FreeState,
                           'options_child': general_states.OptionsChildState,
                           'phase_change': general_states.PhaseChangeState,
                           'move': general_states.MoveState,
                           'movement': general_states.MovementState,
                           'wait': general_states.WaitState,
                           'canto_wait': general_states.CantoWaitState,
                           'menu': general_states.MenuState,
                           'item': general_states.ItemState,
                           'item_child': general_states.ItemChildState
                           }
        if starting_states:
            for state_name in starting_states:
                self.state.append(self.all_states[state_name](state_name))

    def change(self, new_state):
        self.temp_state.append(new_state)

    def back(self):
        self.temp_state.append('pop')

    def clear(self):
        self.temp_state.append('clear')

    def refresh(self):
        # Clears all states except the top one
        self.state = self.state[-1:]

    def get(self):
        if self.state:
            return self.state[-1].name

    def process_temp_state(self):
        for transition in self.temp_state:
            if transition == 'pop':
                if self.state:
                    state = self.state[-1]
                    if state.processed:
                        state.processed = False
                        state.end()
                    state.finish()
                    self.state.pop()
            elif transition == 'clear':
                for state in reversed(self.state):
                    if state.processed:
                        state.processed = False
                        state.end()
                    state.finish()
                self.state.clear()
            else:
                new_state = self.all_states[transition](transition)
                self.state.append(new_state)
        self.temp_state.clear()

    def update(self, event, surf):
        if not self.state:
            return None, False
        state = self.state[-1]
        repeat_flag = False  # Whether we run the state machine again in the same frame
        # Start
        if not state.started:
            state.started = True
            start_output = state.start()
            if start_output == 'repeat':
                repeat_flag = True
        # Begin
        if not repeat_flag and not state.processed:
            state.processed = True
            begin_output = state.begin()
            if begin_output == 'repeat':
                repeat_flag = True
        # Take Input
        if not repeat_flag:
            input_output = state.take_input(event)
            if input_output == 'repeat':
                repeat_flag = True
        # Update
        if not repeat_flag:
            update_output = state.update()
            if update_output == 'repeat':
                repeat_flag = True
        # Draw
        if not repeat_flag:
            if state.transparent and len(self.state) >= 2:
                surf = self.state[-2].draw(surf)
            surf = state.draw(surf)
        # End
        if self.temp_state and state.processed:
            state.processed = False
            state.end()
        # Finish
        self.process_temp_state()  # This is where FINISH is taken care of
        return surf, repeat_flag

    def serialize(self):
        return [state.name for state in self.state], self.temp_state
