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
