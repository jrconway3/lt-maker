class AnimationCombat(BaseCombat):
    alerts: bool = True

    def __init__(self, attacker: UnitObject, main_item: ItemObject, main_target: tuple, script):
        self.attacker = attacker
        self.defender = game.board.get_unit(main_target)
        self.main_item = main_item
        self.def_item = self.defender.get_weapon()

        if self.attacker.team == 'player' and self.defender.team != 'player':
            self.right = self.defender
            self.right_item = self.def_item
            self.left = self.attacker
            self.left_item = self.main_item
        elif self.attacker.team.startswith('enemy') and not self.defender.team.startswith('enemy'):
            self.right = self.defender
            self.right_item = self.def_item
            self.left = self.attacker
            self.left_item = self.main_item
        else:
            self.right = self.attacker
            self.right_item = self.main_item
            self.left = self.defender
            self.left_item = self.def_item

        if self.attacker.position and self.defender.position:
            self.distance = utils.calculate_distance(self.attacker.position, self.defender.position)
        else:
            self.distance = 1
        self.at_range = self.distance - 1

        if self.defender.position:
            self.view_pos = self.defender.position
        elif self.attacker.position:
            self.view_pos = self.attacker.position
        else:
            self.view_pos = (0, 0)

        self.state_machine = CombatPhaseSolver(
            self.attacker, self.main_item, [self.main_item],
            [self.defender], [[]], [self.defender.position],
            self.defender, self.def_item, script)

        self.last_update = engine.get_time()
        self.state = 'init'

        self._skip = False
        self.full_playback = []
        self.playback = []
        self.actions = []

        self.viewbox_time = 250
        self.viewbox = None

        self.bar_offset = 0
        self.name_offset = 0

        self.initial_paint_setup()

    def skip(self):
        self._skip = True

    def update(self) -> bool:
        current_time = engine.get_time() - self.last_update

        if self.state == 'init':
            self.start_combat()
            self.attacker.sprite.change_state('combat_attacker')
            self.defender.sprite.change_state('combat_defender')
            self.state = 'red_cursor'
            self.last_update = engine.get_time()
            game.cursor.combat_show()
            game.cursor.set_pos(self.view_pos)
            if not self._skip:
                game.state.change('move_camera')

        elif self.state == 'red_cursor':
            if self._skip or current_time > 400:
                game.cursor.hide()
                game.highlight.remove_highlights()
                self.state = 'fade_in'

        elif self.state == 'fade_in':
            if current_time <= self.viewbox_time:
                self.build_viewbox(current_time)
            else:
                self.state = 'entrance'
                left_pos = (self.left.position[0] - game.camera.get_x()) * TILEWIDTH, \
                    (self.left.position[1] - game.camera.get_y()) * TILEHEIGHT
                right_pos = (self.right.position[0] - game.camera.get_x()) * TILEWIDTH, \
                    (self.right.position[1] - game.camera.get_y()) * TILEHEIGHT
                self.left_battle_anim.pair(self, self.right_battle_anim, self.at_range, left_pos)
                self.right_battle_anim.pair(self, self.left_battle_anim, self.at_range, right_pos)
                # Unit should be facing down
                self.attacker.change_state('selected')
                self.last_update = engine.get_time()

        elif self.state == 'entrance':
            entrance_time = 400
            self.bar_offset = current_time / entrance_time
            self.name_offset = current_time / entrance_time
            if self._skip or current_time > entrance_time:
                self.bar_offset = 1
                self.name_offset = 1
                self.last_update = engine.get_time()
                self.state = 'init_pause'
                self.start_battle_music()

        elif self.state == 'init_pause':
            if self._skip or current_time > 410:  # 25 frames
                self.last_update = engine.get_time()
                self.state = 'pre_proc'

        elif self.state == 'pre_proc':
            if self.left_battle_anim.done() and self.right_battle_anim.done():
                if self.state_machine.get_attacker_pre_proc():
                    self.set_up_pre_proc_animation(self.attacker, self.state_machine.get_attacker_pre_proc())
                elif self.state_machine.get_defender_pre_proc():
                    self.set_up_pre_proc_animation(self.defender, self.state_machine.get_defender_pre_proc())
                else:
                    self.state = 'init_effects'
                    self.last_update = engine.get_time()

        elif self.state == 'init_effects':
            if not self.left_battle_anim.effect_playing() and not self.right_battle_anim.effect_playing():
                if self.right_item:
                    effect = item_system.combat_effect(self.right, self.right_item, self.left)
                    self.right_battle_anim.add_effect(effect)
                elif self.left_item:
                    effect = item_system.combat_effect(self.left, self.left_item, self.right)
                    self.left_battle_anim.add_effect(effect)
                else:
                    self.last_update = engine.get_time()
                    self.state = 'begin_phase'

        elif self.state == 'begin_phase':
            # Get playback
            if not self.state_machine.get_state():
                self.clean_up()
                return True
            self.actions, self.playback = self.state_machine.do()
            self.full_playback += self.playback
            if not self.actions and not self.playback:
                self.state_machine.setup_next_state()
                return False
            self._set_stats()

            if self.get_from_playback('attack_proc'):
                self.state = 'attack_proc'
            elif self.get_from_playback('defense_proc'):
                self.state = 'defense_proc'
            else:
                self.set_up_animation()
            self.last_update = engine.get_time()

        elif self.state == 'attack_proc':
            if self.left_battle_anim.done() and self.right_battle_anim.done() and current_time > 400:
                if self.get_from_playback('defense_proc'):
                    self.state = 'defense_proc'
                else:
                    self.set_up_animation()
                self.last_update = engine.get_time()

        elif self.state == 'defense_proc':
            if self.left_battle_anim.done() and self.right_battle_anim.done() and current_time > 400:
                self.set_up_animation()
                self.last_update = engine.get_time()

        elif self.state == 'anim':
            if self.left_battle_anim.done() and self.right_battle_anim.done():
                self.state = 'end_phase'
                self.last_update = engine.get_time()







    def build_viewbox(self, current_time):
        vb_multiplier = current_time / self.viewbox_time
        true_x, true_y = self.view_pos[0] - game.camera.get_x(), self.view_pos[1] - game.camera.get_y()
        vb_x = vb_multiplier * true_x * TILEWIDTH
        vb_y = vb_multiplier * true_y * TILEHEIGHT
        vb_width = WINWIDTH - vb_x - (vb_multiplier * (TILEX - true_x)) * TILEWIDTH
        vb_height = WINHEIGHT - vb_y - (vb_multiplier * (TILEY - true_y)) * TILEHEIGHT
        self.viewbox = (vb_x, vb_y, vb_width, vb_height)
