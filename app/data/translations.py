from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class Translation(Prefab):
    nid: str = None
    text: str = ""

class TranslationCatalog(Data):
    datatype = Translation
