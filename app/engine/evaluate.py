import random

from app.utilities import utils
from app.data.database import DB

import app.engine.config as cf
from app.engine import engine, item_funcs, item_system, skill_system, combat_calcs, unit_funcs
from app.engine.game_state import game

"""
Essentially just a repository that imports a lot of different things so that many different eval calls 
will be accepted
"""

def evaluate(string: str, unit1=None, unit2=None, item=None, position=None, region=None, mode=None) -> bool:
    unit = unit1
    target = unit2
    
    def check_pair(s1: str, s2: str) -> bool:
        """
        Determines whether two units are in combat with one another
        """
        return (unit1.nid == s1 and unit2.nid == s2) or (unit1.nid == s2 and unit2.nid == s1)

    def check_default(s1: str, t1: tuple) -> bool:
        """
        Determines whether the default fight quote should be used
        t1 contains the nids of units that have unique fight quotes
        """
        if unit1.nid == s1 and unit2.team == 'player':
            return unit2.nid not in t1
        elif unit2.nid == s1 and unit1.team == 'player':
            return unit1.nid not in t1
        else:
            return False

    return eval(string)
