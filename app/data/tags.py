from dataclasses import dataclass

from app.data.data import Data, Prefab
from app import utilities

@dataclass
class Tag(Prefab):
    nid: str = None

    def serialize(self):
        return self.nid

    @classmethod
    def deserialize(cls, s_val):
        return cls(s_val)

class TagCatalog(Data):
    datatype = Tag

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('Tag', self.keys())
        new_tag = Tag(new_row_nid)
        self.append(new_tag)
