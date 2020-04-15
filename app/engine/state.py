from app.engine.game_state import game

class State():
    name = None
    in_level = True
    show_map = True
    transparent = False

    started = False
    processed = False

    def __init__(self, name=None):
        if name:
            self.name = name

    def start(self):
        pass

    def begin(self):
        pass

    def take_input(self, event):
        pass

    def update(self):
        pass

    def draw(self, surf):
        return surf

    def end(self):
        pass

    def finish(self):
        pass

class MapState(State):
    def update(self):
        game.cursor.update()
        game.camera.update()
        # game.tilemap.update()
        game.highlight.update()
        game.map_view.update()

    def draw(self, surf):
        surf = game.map_view.draw()
        return surf
