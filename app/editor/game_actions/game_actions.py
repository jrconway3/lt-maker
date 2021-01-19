import glob

from app.editor.data_editor import DB
from app.engine import driver, game_state

def test_play():
    title = DB.constants.get('title').value
    driver.start(title, from_editor=True)
    game = game_state.start_game()
    driver.run(game)


def test_play_current(level_nid):
    from app.engine import driver, game_state
    title = DB.constants.get('title').value
    driver.start(title, from_editor=True)
    game = game_state.start_level(level_nid)
    driver.run(game)


def get_saved_games():
    GAME_NID = str(DB.constants.value('game_nid'))
    return glob.glob('saves/' + GAME_NID + '-preload-*-*.p')


def test_play_load(level_nid, save_loc=None):
    title = DB.constants.get('title').value
    driver.start(title, from_editor=True)
    if save_loc:
        game = game_state.load_level(level_nid, save_loc)
    else:
        game = game_state.start_level(level_nid)
    driver.run(game)
