from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.editor.base_database_gui import DragDropCollectionModel
import app.editor.utilities as editor_utilities
from app.utilities import str_utils

from app.data import factions

def get_pixmap(faction):
    x, y = faction.icon_index
    res = RESOURCES.icons32.get(faction.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x*32, y*32, 32, 32)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class FactionModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            faction = self._data[index.row()]
            text = faction.nid
            return text
        elif role == Qt.DecorationRole:
            faction = self._data[index.row()]
            pixmap = get_pixmap(faction)
            if pixmap:
                return QIcon(pixmap)
        return None

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Faction", nids)
        new_faction = factions.Faction(nid, name)
        DB.factions.append(new_faction)
        return new_faction
