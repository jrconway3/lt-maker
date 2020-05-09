from app.engine.sprites import SPRITES
from app.engine.state import State
from app.engine import background, image_mods

from app.engine.game_state import game

class GameOver(State):
    name = 'game_over'

    def start(self):
        """
        Displays the game over screen for a little transition,
        then cut to start screen
        """
        initial_state = 'text_fade_in'
        self.state = initial_state
        self.transparency = 100
        # Music

        self.text_surf = SPRITES.get('game_over_text')

        self.bg = background.TransitionBackground(SPRITES.get('game_over_bg'))
        game.memory['transition_speed'] = 0.01
        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        if self.state == 'stasis' and event:
            game.state.back()  # Any input returns to start screen

    def update(self):
        if self.state == 'text_fade_in':
            self.transparency -= 2
            if self.transparency <= 0:
                self.transparency = 0
                self.state = 'bg_fade_in'
        elif self.state == 'bg_fade_in':
            if self.bg.update():
                self.state = 'stasis'
        elif self.state == 'stasis':
            self.bg.update()

    def draw(self, surf):
        self.bg.draw(surf)
        text_surf = image_mods.make_translucent(self.text_surf, self.transparency / 100.)
        surf.blit(text_surf)
        surf.blit(SPRITES.get('game_over_fade'), (0, 0))
        return surf
