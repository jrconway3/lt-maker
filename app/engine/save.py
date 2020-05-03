import os, shutil
import threading

from app.data.items import Item
from app.data.database import DB

import app.engine.config as cf

import logging
logger = logging.getLogger(__name__)

SAVE_THREAD = None
SUSPEND_LOC = 'saves/suspend.pmeta'

class SaveSlot():
    no_name = '--NO DATA--'

    def __init__(self, metadata_fn, num):
        self.name = self.no_name
        self.playtime = 0
        self.realtime = 0
        self.kind = None  # Prep, Base, Suspend, Battle, Start
        self.number = num

        self.meta_loc = metadata_fn
        self.save_loc = metadata_fn[:-4]

        self.read()

    def read(self):
        if os.path.exists(self.meta_loc):
            with open(self.meta_loc, 'rb') as fp:
                save_metadata = pickle.load(fp)
            self.name = save_metadata['level_title']
            self.playtime = save_metadata['playtime']
            self.realtime = save_metadata['realtime']
            self.kind = save_metadata['kind']
            if self.number is None:
                self.number = save_metadata['save_slot']

    def get_name(self):
        if self.kind:
            return self.name + ' - ' + self.kind
        else:
            return self.name

def save_io(s_dict, meta_dict, slot=None, force_loc=None):
    if force_loc:
        save_loc = 'saves/' + force_loc + '.p'
        meta_loc = 'saves/' + force_loc + '.pmeta'
    elif slot:
        save_loc = 'saves/save_state' + str(slot) + '.p'
        meta_loc = 'saves/save_state' + str(slot) + '.pmeta'

    logger.info("Saving to %s", save_loc)

    with open(save_loc, 'wb') as fp:
        # pickle.dump(s_dict, fp, -1)
        pickle.dump(s_dict, fp)
    with open(meta_loc, 'wb') as fp:
        pickle.dump(meta_dict, fp)

    # For restart
    # if slot:
    #     r_save = 'saves/restart' + str(slot) + '.p'
    #     r_save_meta = 'saves/restart' + str(slot) + '.pmeta'
    #     # If the slot I'm overwriting is a start of map
    #     if old_slot == 'start':
    #         # Then rename it to restart file
    #         if save_loc != r_save:
    #             shutil.copy(save_loc, r_save)
    #             shutil.copy(meta_loc, r_save_meta)
    #     else:  # 
    #         old_name = 'saves/restart' + str(old_slot) + '.p'
    #         if old_name != r_save:
    #             shutil.copy(old_name, r_save)
    #             shutil.copy(old_name + 'meta', r_save_meta)

def suspend_game(game_state, kind, slot=None):
    """
    Saves game state to file
    """
    s_dict, meta_dict = game_state.save()
    meta_dict['kind'] = kind

    if kind == 'suspend':
        force_loc = 'suspend'
    else:
        force_loc = None

    SAVE_THREAD = threading.Thread(target=save_io, args=(s_dict, meta_dict, slot, force_loc))
    SAVE_THREAD.start()

def load_game(game_state, save_slot):
    """
    Load game state from file
    """
    save_loc = save_slot.fn_loc
    with open(save_loc, 'rb') as fp:
        s_dict = pickle.load(fp)
    game_state.load(s_dict)
    game_state.current_save_slot = save_slot

    set_next_uids(game_state)

def set_next_uids(game_state):
    if game_state.item_registry:
        Item.next_uid = max(game_state.item_registry.keys()) + 1
    else:
        Item.next_uid = 100
    if game_state.status_registry:
        Status.next_uid = max(game_state.status_registry.keys()) + 1
    else:
        Status.next_uid = 100

def load_saves():
    save_slots = []
    for num in range(0, int(DB.constants.get('num_save_slots').value)):
        meta_fp = 'saves/save_state' + str(num) + '.pmeta'
        ss = SaveSlot(meta_fp, num)
        save_slots.append(ss)
    return save_slots

def load_restarts():
    save_slots = []
    for num in range(0, int(DB.constants.get('num_save_slots').value)):
        meta_fp = 'saves/restart' + str(num) + '.pmeta'
        ss = SaveSlot(meta_fp, num)
        save_slots.append(ss)
    return save_slots

def remove_suspend():
    if not cf.SETTINGS['debug'] and os.path.exists(SUSPEND_LOC):
        os.remove(SUSPEND_LOC)

def get_save_title(save_slots):
    options = [save_slot.get_name() for save_slot in save_slots]
    colors = ['green' for save_slot in save_slots]
    return options, colors

def check_save_slots(self):
    global SAVE_SLOTS, RESTART_SLOTS
    SAVE_SLOTS = load_saves()
    RESTART_SLOTS = load_restarts()

SAVE_SLOTS = load_saves()
RESTART_SLOTS = load_restarts()
