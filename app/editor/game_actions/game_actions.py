import glob

from app.editor.data_editor import DB
from app.engine import engine, driver, game_state

import logging

def handle_exception(e: Exception):
    logging.error("Engine crashed with a fatal error!")
    logging.exception(e)
    # Required to close window (reason: Unknown)
    engine.terminate(True)

def test_play():
    title = DB.constants.value('title')
    try:
        driver.start(title, from_editor=True)
        game = game_state.start_game()
        driver.run(game)
    except Exception as e:
        handle_exception(e)

def test_play_current(level_nid):
    title = DB.constants.value('title')
    try:
        driver.start(title, from_editor=True)
        game = game_state.start_level(level_nid)
        driver.run(game)
    except Exception as e:
        handle_exception(e)

def get_saved_games():
    GAME_NID = str(DB.constants.value('game_nid'))
    return glob.glob('saves/' + GAME_NID + '-preload-*-*.p')

def test_play_load(level_nid, save_loc=None):
    title = DB.constants.value('title')
    try:
        driver.start(title, from_editor=True)
        if save_loc:
            game = game_state.load_level(level_nid, save_loc)
        else:
            game = game_state.start_level(level_nid)
        driver.run(game)
    except Exception as e:
        handle_exception(e)

def test_combat(left_weapon_anim, left_palette, left_item_nid: str, 
                right_weapon_anim, right_palette, right_item_nid: str):
    from app.engine.battle_animation import BattleAnimation
    from app.engine.combat.mock_combat import MockCombat
    try:
        driver.start("Combat Test", from_editor=True)
        right = BattleAnimation(right_weapon_anim, right_palette, None, right_item_nid)
        left = BattleAnimation(left_weapon_anim, left_palette, None, left_item_nid)
        at_range = 1 if 'Ranged' in right_weapon_anim.nid else 0
        mock_combat = MockCombat(left, right)
        left.pair(mock_combat, right, False, at_range)
        right.pair(mock_combat, left, True, at_range)
        driver.run_combat(mock_combat)
    except Exception as e:
        handle_exception(e)
