from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class Tag(Prefab):
    nid: str = None

    def save(self):
        return self.nid

    @classmethod
    def restore(cls, dat):
        return cls(dat)

class TagCatalog(Data):
    datatype = Tag

    def __init__(self, strs):
        super().__init__()
        for s in strs:
            self.append(Tag(s))
