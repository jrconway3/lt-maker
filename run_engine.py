import os

from app.data.constants import VERSION
from app.data.resources import RESOURCES
from app.data.database import DB
from app.engine import engine
from app.engine import config as cf
from app.engine import game_state

def main():
    RESOURCES.load()
    DB.deserialize()
    title = DB.constants.get('title').value
    engine.start(title)
    game = game_state.start_game()
    engine.run(game)

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
    logging_level = logging.DEBUG if cf.SETTINGS['debug'] else logging.WARNING
    logging.basicConfig(filename='saves/debug.log.1', filemode='w', level=logging_level, 
                        format='%(relativeCreated)d %(levelname)7s:%(module)16s: %(message)s')
    logger.info('*** Lex Talionis Engine Version %s ***' % VERSION)
    try:
        main()
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
