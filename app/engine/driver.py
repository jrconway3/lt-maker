from app.data.constants import WINWIDTH, WINHEIGHT, VERSION
from app.engine import engine

import app.engine.config as cf

def start(title, from_editor=False):
    if from_editor:
        engine.constants['standalone'] = False
    engine.init()
    icon = engine.image_load('main_icon.ico')
    engine.set_icon(icon)
    engine.DISPLAYSURF = engine.build_display(engine.SCREENSIZE)
    engine.set_title(title + ' - v' + VERSION)
    print("Version: %s" % VERSION)

def run(game):
    from app.engine.sound import SOUNDTHREAD
    SOUNDTHREAD.set_music_volume(cf.SETTINGS['music_volume'])
    surf = engine.create_surface((WINWIDTH, WINHEIGHT))
    # import time
    while True:
        # start = time.time_ns()
        engine.update_time()

        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break
        event = game.input_manager.process_input(raw_events)

        surf, repeat = game.state.update(event, surf)
        while repeat:  # Let's the game traverse through state chains
            surf, repeat = game.state.update([], surf)

        SOUNDTHREAD.update(raw_events)

        engine.push_display(surf, engine.SCREENSIZE, engine.DISPLAYSURF)
        engine.update_display()
        # end = time.time_ns()
        # milliseconds_elapsed = (end - start)/1e6
        # if milliseconds_elapsed > 10:
        #     print("Engine took too long: %f" % milliseconds_elapsed)

        game.playtime += engine.tick()
