from dataclasses import dataclass, field
from typing import Tuple, List

from app.utilities.data import Data, Prefab
from app.utilities import str_utils

@dataclass
class Credit(Prefab):
    nid: str = None
    sub_nid: str = None
    type: str = "16x16_Icons"
    category: str = "Graphics"

    icon_index: Tuple[int, int] = field(default_factory=tuple)
    contrib: List[List] = field(default_factory=list) # each list is a tuple (author, contribution)

class CreditCatalog(Data[Credit]):
    datatype = Credit

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = sub_nid = str_utils.get_next_name("New Credit", nids)
        new_credit = Credit(nid, sub_nid)
        self.append(new_credit)
        return new_credit
