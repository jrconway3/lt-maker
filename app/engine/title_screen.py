from app.data.resources import RESOURCES

from app.engine import engine
from app.engine.sprites import SPRITES
from app.engine.state import State
from app.engine.background import PanoramaBackground
from app.engine.game_state import game

class TitleStartState(State):
    name = "title_start"
    in_level = False
    show_map = False

    def start(self):
        self.logo = SPRITES.get('logo')
        imgs = RESOURCES.panoramas.get('title_background')
        self.bg = PanoramaBackground(imgs) if imgs else None
        game.memory['transition_speed'] = 0.01
        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        if event:
            game.state.change('title_main')
            game.state.change('transition_out')

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        engine.blit_center(surf, self.logo)
        return surf
