import os
import logging

from app.constants import VERSION
from app.engine import config as cf

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

def create_logger():
    logger = logging.getLogger(__name__)
    try:
        create_debug_log()
    except WindowsError:
        print("Error! Debug logs in use -- Another instance of this is already running!")
        return None
    except PermissionError:
        print("Error! Debug logs in use -- Another instance of this is already running!")
        return None
    logging_level = logging.DEBUG if cf.SETTINGS['debug'] else logging.WARNING
    logging.basicConfig(handlers=[logging.FileHandler('saves/debug.log.1', 'w', 'utf-8')],
                        level=logging_level, format='%(relativeCreated)d %(levelname)7s:%(module)16s: %(message)s')
    logger.info('*** Lex Talionis Engine Version %s ***' % VERSION)
    return logger
