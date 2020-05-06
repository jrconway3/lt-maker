import logging
logger = logging.getLogger(__name__)

class SimpleStateMachine():
    def __init__(self, starting_state):
        self.state = []
        self.state.append(starting_state)

    def change(self, new_state):
        self.state.append(new_state)

    def back(self):
        self.state.pop()

    def get_state(self):
        if self.state:
            return self.state[-1]
        return None

    def clear(self):
        self.state.clear()

class StateMachine():
    def __init__(self):
        self.state = []
        self.temp_state = []

    def load_states(self, starting_states=None, temp_state=None):
        from app.engine import title_screen, transitions, general_states, level_up, turnwheel
        self.all_states = {'title_start': title_screen.TitleStartState,
                           'title_main': title_screen.TitleMainState,
                           'title_load': title_screen.TitleLoadState,
                           'title_restart': title_screen.TitleRestartState,
                           'title_new': title_screen.TitleNewState,
                           'title_new_child': title_screen.TitleNewChildState,
                           'title_extras': title_screen.TitleExtrasState,
                           'title_wait': title_screen.TitleWaitState,
                           'title_save': title_screen.TitleSaveState,
                           'transition_in': transitions.TransitionInState,
                           'transition_out': transitions.TransitionOutState,
                           'transition_pop': transitions.TransitionPopState,
                           'transition_double_pop': transitions.TransitionDoublePopState,
                           'transition_to': transitions.TransitionToState,
                           'turn_change': general_states.TurnChangeState,
                           'free': general_states.FreeState,
                           'option_menu': general_states.OptionMenuState,
                           'option_child': general_states.OptionChildState,
                           'phase_change': general_states.PhaseChangeState,
                           'move': general_states.MoveState,
                           'movement': general_states.MovementState,
                           'wait': general_states.WaitState,
                           'canto_wait': general_states.CantoWaitState,
                           'move_camera': general_states.MoveCameraState,
                           'dying': general_states.DyingState,
                           'menu': general_states.MenuState,
                           'item': general_states.ItemState,
                           'item_child': general_states.ItemChildState,
                           'rescue_select': general_states.SelectState,
                           'drop_select': general_states.SelectState,
                           'give_select': general_states.SelectState,
                           'take_select': general_states.SelectState,
                           'trade_select': general_states.SelectState,
                           'trade': general_states.TradeState,
                           'weapon_choice': general_states.WeaponChoiceState,
                           'spell_choice': general_states.SpellChoiceState,
                           'attack': general_states.AttackState,
                           'spell': general_states.SpellState,
                           'combat': general_states.CombatState,
                           'display_alerts': general_states.DisplayAlertsState,
                           'ai': general_states.AIState,
                           'exp': level_up.ExpState,
                           'turnwheel': turnwheel.TurnwheelState,
                           }
        if starting_states:
            for state_name in starting_states:
                self.state.append(self.all_states[state_name](state_name))
        if temp_state:
            self.temp_state = temp_state

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

    def get_state(self):
        if self.state:
            return self.state[-1].name

    def process_temp_state(self):
        if self.temp_state:
            logger.info("Temp State: %s", self.temp_state)
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
        if self.temp_state:
            logger.info("State: %s", [s.name for s in self.state])
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
