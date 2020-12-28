import os

from app.constants import VERSION
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.engine import engine
from app.engine import config as cf
from app.engine import driver
from app.engine import game_state

def main():
    RESOURCES.load('./default.ltproj')
    DB.load('./default.ltproj')
    title = DB.constants.value('title')
    driver.start(title)
    game = game_state.start_game()
    driver.run(game)

def test_play():
    RESOURCES.load('./sacred_stones.ltproj')
    DB.load('./sacred_stones.ltproj')
    title = DB.constants.value('title')
    driver.start(title, from_editor=True)
    game = game_state.start_level('1')
    driver.run(game)

def create_debug_log():
    """
    Increments all old debug logs in number
    Destroys logs older than 5 runs
    """
    counter = 5  # traverse backwards, so we don't overwrite older logs
    while counter > 0:
        fn = 'saves/debug.log.' + str(counter)
        if os.path.exists(fn):
            if counter == 5:
                os.remove(fn)
            else:
                os.rename(fn, 'saves/debug.log.' + str(counter + 1))
        counter -= 1

def inform_error():
    print("=== === === === === ===")
    print("A bug has been encountered.")
    print("Please copy this error log and send it to rainlash!")
    print('Or send the file "saves/debug.log.1" to rainlash!')
    print("Thank you!")
    print("=== === === === === ===")

if __name__ == '__main__':
    import logging, traceback
    logger = logging.getLogger(__name__)
    try:
        create_debug_log()
    except WindowsError:
        print("Error! Debug logs in use -- Another instance of this is already running!")
        engine.terminate()
    except PermissionError:
        print("Error! Debug logs in use -- Another instance of this is already running!")
        engine.terminate()
    logging_level = logging.DEBUG if cf.SETTINGS['debug'] else logging.WARNING
    logging.basicConfig(handlers=[logging.FileHandler('saves/debug.log.1', 'w', 'utf-8')],
                        level=logging_level, format='%(relativeCreated)d %(levelname)7s:%(module)16s: %(message)s')
    logger.info('*** Lex Talionis Engine Version %s ***' % VERSION)
    try:
        # main()
        test_play()
    except Exception as e:
        logger.exception(e)
        inform_error()
        print('*** Lex Talionis Engine Version %s ***' % VERSION)
        print('Main Crash {0}'.format(str(e)))

        # Now print exception to screen
        import time
        time.sleep(0.5)
        traceback.print_exc()
        time.sleep(0.5)
        engine.on_end(crash=True)
        inform_error()
        if cf.SETTINGS['debug']:
            time.sleep(5)
        else:
            time.sleep(20)
