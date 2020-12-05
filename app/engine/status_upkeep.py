from app.resources.resources import RESOURCES
from app.engine.sound import SOUNDTHREAD
from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import engine, action, skill_system, \
    health_bar, animations

import logging
logger = logging.getLogger(__name__)

class StatusUpkeepState(MapState):
    name = 'status_upkeep'

    def start(self):
        logger.info("Starting Status Upkeep State")
        game.cursor.hide()
        self.units = [unit for unit in game.level.units if not unit.dead and unit.position]
        self.cur_unit = None

        self.health_bar = None
        self.animations = []

        self.last_update = 0
        self.time_for_change = 0

    def update(self):
        super().update()

        if self.health_bar:
            self.health_bar.update()

        if self.state == 'processing':
            # Don't bother if someone is dying!!!
            if any(unit.is_dying for unit in game.level.units):
                return

            if (not self.cur_unit or not self.cur_unit.position) and self.units:
                self.cur_unit = self.units.pop()

            if self.cur_unit:
                actions, playback = [], []
                skill_system.on_upkeep(actions, playback, self.cur_unit)
                if (actions or playback) and self.cur_unit.position:
                    self.health_bar = health_bar.MapHealthBar(self.cur_unit)
                    self.handle_playback(playback)
                    for act in actions:
                        action.do(act)
                    self.health_bar.update()  # Force update to get time for change
                    self.state = 'running'
                    self.last_update = engine.get_time()
                    self.time_for_change = self.health_bar.time_for_change
                else:
                    return 'repeat'

            else:
                game.state.back()
                return 'repeat'

        elif self.state == 'running':
            if engine.get_time() > self.last_update + self.time_for_change:
                self.state = 'processing'
                self.cur_unit = None

    def handle_playback(self, playback):
        for brush in playback:
            if brush[0] == 'unit_tint':
                color = brush[2]
                brush[1].sprite.begin_flicker(333, color)
            elif brush[0] == 'cast_sound':
                SOUNDTHREAD.play_sfx(brush[1])
            elif brush[0] == 'cast_anim':
                anim = RESOURCES.animations.get(brush[1])
                pos = game.cursor.position
                if anim:
                    anim = animations.MapAnimation(anim, pos)
                    self.animations.append(anim)

    def draw(self, surf):
        surf = super().draw(surf)
        if self.health_bar:
            self.health_bar.draw(surf)

        self.animations = [anim for anim in self.animations if not anim.update()]
        for anim in self.animations:
            anim.draw(surf)

        return surf
