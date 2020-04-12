from app.data.constants import WINWIDTH, WINHEIGHT, VERSION
from app.engine import engine
from app.engine.input_manager import INPUT

def start(title, from_editor=False):
    if from_editor:
        engine.constants['standalone'] = False
    engine.init()
    icon = engine.image_load('main_icon.png')
    engine.set_icon(icon)
    engine.DISPLAYSURF = engine.build_display(engine.SCREENSIZE)
    engine.set_title(title + ' - v' + VERSION)
    INPUT.start()
    print("Version: %s" % VERSION)

def run(game):
    surf = engine.create_surface((WINWIDTH, WINHEIGHT))
    while True:
        engine.update_time()

        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break
        event = INPUT.process_input(raw_events)

        surf, repeat = game.state.update(event, surf)
        while repeat:  # Let's the game traverse through state chains
            surf, repeat = game.state.update([], surf)

        engine.push_display(surf, engine.SCREENSIZE, engine.DISPLAYSURF)
        engine.update_display()

        game.playtime += engine.tick()
