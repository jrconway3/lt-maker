import random

from app.utilities import utils
from app.data.database import DB

import app.engine.config as cf
from app.engine import engine, item_funcs, item_system, skill_system, combat_calcs, item_funcs
from app.engine.game_state import game

"""
Essentially just a repository that imports a lot of different things so that many different eval calls 
will be accepted
"""

def evaluate(string: str, unit1=None, unit2=None, item=None, position=None, region=None) -> bool:
    unit = unit1
    return eval(string)
