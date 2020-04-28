from dataclasses import dataclass

from app.data.data import Data, Prefab
from app import utilities

@dataclass
class Translation(Prefab):
    nid: str = None
    text: str = ""

class TranslationCatalog(Data):
    datatype = Translation

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('Word', self.keys())
        new_translation = Translation(new_row_nid, "Word")
        self.append(new_translation)
        return new_translation
