from dataclasses import dataclass

from app.utilities.data import Data, Prefab
from app.utilities import str_utils

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

    def add_new_default(self, db):
        nid = str_utils.get_next_name("New Stat", self.keys())
        new_stat = StatPrefab(nid, nid)
        self.append(new_stat)
        return new_stat

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

    @classmethod
    def default(cls, db, starting_value=0):
        return cls([Stat(nid, starting_value) for nid in db.stats.keys()])

    def new_key(self, idx, nid):
        new_stat = Stat(nid, 0)
        self.insert(idx, new_stat)
