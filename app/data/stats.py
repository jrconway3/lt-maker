from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class StatPrefab(Prefab):
    nid: str = None
    name: str = None
    maximum: int = 30
    desc: str = ""

    def __repr__(self):
        return self.nid

class StatCatalog(Data):
    datatype = StatPrefab

@dataclass
class Stat(Prefab):
    nid: str = None
    value: int = 10

    def __str__(self):
        return str(self.value)

    def save(self):
        return (self.nid, self.value)

    @classmethod
    def restore(cls, s_tuple):
        return cls(*s_tuple)

class StatList(Data):
    datatype = Stat
