import functools
from enum import IntEnum

from app.data.data import Data

class Type(IntEnum):
    Int = 1
    Float = 2
    String = 3
    WeaponType = 4  # Stored as Nids
    WeaponRank = 5  # Stored as Nids
    Unit = 6  # Stored as Nids
    Class = 7  # Stored as Nids
    Tag = 8
    Color3 = 9
    Color4 = 10
    Item = 12  # Stored as Nids
    Status = 13  # Stored as Nids
    Stat = 14  # Stored as Nids
    List = 100
    Dict = 101

tags = ['base', 'target', 'weapon', 'uses', 'extra', 'exp', 'aoe', 'aesthetic', 'advanced', 'custom']

class ItemComponent():
    nid: str = None
    desc: str = None
    author: str = 'rainlash'
    expose = None  # Attribute for the Item Component
    requires: list = None
    tag = 'extra'
    value = None

    def __init__(self, value=None):
        self.value = value

    @property
    def name(self):
        name = self.__class__.__name__
        print(name)
        name = functools.reduce(lambda a, b: a + ((b.upper() == b and (a and a[-1].upper() != a[-1])) and (' ' + b) or b), name, '')
        return name

    @classmethod
    def class_name(cls):
        name = cls.__name__
        print(name)
        name = functools.reduce(lambda a, b: a + ((b.upper() == b and (a and a[-1].upper() != a[-1])) and (' ' + b) or b), name, '')
        return name

    def defines(self, function_name):
        return hasattr(self, function_name)

    @classmethod
    def copy(cls, other):
        return cls(other.value)

    def serialize(self):
        if isinstance(self.value, Data):
            return self.nid, self.value.save()
        else:
            return self.nid, self.value
