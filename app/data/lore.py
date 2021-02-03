from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class Lore(Prefab):
    nid: str = None
    name: str = None
    title: str = None
    text: str = ""

class LoreCatalog(Data):
    datatype = Lore
