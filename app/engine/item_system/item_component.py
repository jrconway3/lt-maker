import functools
from enum import IntEnum

class Type(IntEnum):
    Int = 1
    Float = 2
    String = 3
    WeaponType = 4
    WeaponRank = 5
    Unit = 6
    Class = 7
    Tag = 8
    Color = 9
    Status = 10
    Set = 100
    Dict = 101

class ItemComponent():
    nid: str = None
    desc: str = None
    author: str = 'rainlash'

    @property
    def name(self):
        name = self.__class__.__name__
        return functools.reduce(lambda a, b: a + ((b.upper() == b and (a and a[-1].upper() != a[-1])) and (' ' + b) or b), name, '')

    def defines(self, function_name):
        return hasattr(self, function_name)