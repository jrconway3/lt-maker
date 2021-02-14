import os, shutil, glob
import threading

try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.utilities import str_utils
from app.data.database import DB

import app.engine.config as cf
from app.engine.objects.item import ItemObject
from app.engine.objects.skill import SkillObject

import logging
logger = logging.getLogger(__name__)

SAVE_THREAD = None
GAME_NID = str(DB.constants.value('game_nid'))
SUSPEND_LOC = 'saves/' + GAME_NID + '-suspend.pmeta'

class SaveSlot():
    no_name = '--NO DATA--'

    def __init__(self, metadata_fn, idx):
        self.name = self.no_name
        self.playtime = 0
        self.realtime = 0
        self.kind = None  # Prep, Base, Suspend, Battle, Start
        self.idx = idx

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

    def get_name(self):
        if self.kind:
            return self.name + ' - ' + self.kind
        else:
            return self.name

def dict_print(d):
    for k, v in d.items():
        if isinstance(v, dict):
            dict_print(v)
        else:
            print("{0} : {1}".format(k, v))

def save_io(s_dict, meta_dict, slot=None, force_loc=None):
    if force_loc:
        save_loc = 'saves/' + GAME_NID + '-' + force_loc + '.p'
    elif slot is not None:
        save_loc = 'saves/' + GAME_NID + '-' + str(slot) + '.p'
    meta_loc = save_loc + 'meta'

    logger.info("Saving to %s", save_loc)

    with open(save_loc, 'wb') as fp:
        # pickle.dump(s_dict, fp, -1)
        dict_print(s_dict)
        pickle.dump(s_dict, fp)
    with open(meta_loc, 'wb') as fp:
        pickle.dump(meta_dict, fp)

    # For restart
    if meta_dict['kind'] == 'start':
        r_save = 'saves/' + GAME_NID + '-restart' + str(slot) + '.p'
        r_save_meta = 'saves/' + GAME_NID + '-restart' + str(slot) + '.pmeta'
        # Handle preload saves
        preload_saves = glob.glob('saves/' + GAME_NID + '-preload-' + str(meta_dict['level_nid']) + '-*.p')
        nids = [p.split('-')[-1][:-2] for p in preload_saves]
        unique_nid = str(str_utils.get_next_int('0', nids))
        preload_save = 'saves/' + GAME_NID + '-preload-' + str(meta_dict['level_nid']) + '-' + unique_nid + '.p'
        preload_save_meta = 'saves/' + GAME_NID + '-preload-' + str(meta_dict['level_nid']) + '-' + unique_nid + '.pmeta'
        # If the slot I'm overwriting is a start of map
        # Then rename it to restart file
        if save_loc != r_save:
            shutil.copy(save_loc, r_save)
            shutil.copy(meta_loc, r_save_meta)
        shutil.copy(save_loc, preload_save)
        shutil.copy(meta_loc, preload_save_meta)

def suspend_game(game_state, kind, slot=None):
    """
    Saves game state to file
    """
    s_dict, meta_dict = game_state.save()
    print(s_dict['state'])
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
    save_loc = save_slot.save_loc
    with open(save_loc, 'rb') as fp:
        s_dict = pickle.load(fp)
    game_state.build_new()
    game_state.load(s_dict)
    game_state.current_save_slot = save_slot

    set_next_uids(game_state)

def set_next_uids(game_state):
    if game_state.item_registry:
        ItemObject.next_uid = max(game_state.item_registry.keys()) + 1
    else:
        ItemObject.next_uid = 100
    if game_state.skill_registry:
        SkillObject.next_uid = max(game_state.skill_registry.keys()) + 1
    else:
        SkillObject.next_uid = 100

def load_saves():
    save_slots = []
    for num in range(0, int(DB.constants.get('num_save_slots').value)):
        meta_fp = 'saves/' + GAME_NID + '-' + str(num) + '.pmeta'
        ss = SaveSlot(meta_fp, num)
        save_slots.append(ss)
    return save_slots

def load_restarts():
    save_slots = []
    for num in range(0, int(DB.constants.get('num_save_slots').value)):
        meta_fp = 'saves/' + GAME_NID + '-restart' + str(num) + '.pmeta'
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

def check_save_slots():
    global SAVE_SLOTS, RESTART_SLOTS
    SAVE_SLOTS = load_saves()
    RESTART_SLOTS = load_restarts()

SAVE_SLOTS = load_saves()
RESTART_SLOTS = load_restarts()
