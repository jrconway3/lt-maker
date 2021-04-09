from PyQt5.QtGui import QPixmap, QIcon, QPainter, QImage
from PyQt5.QtCore import Qt

from app.data.database import DB
from app.data import supports

from app.editor.unit_editor import unit_model
from app.editor.base_database_gui import DragDropCollectionModel

def get_pixmap(support_pair):
    unit1_chibi, unit2_chibi = None, None
    if support_pair.unit1 and support_pair.unit1 in DB.units.keys():
        unit1_chibi = unit_model.get_chibi(support_pair.unit1)
    if support_pair.unit2 and support_pair.unit2 in DB.units.keys():
        unit2_chibi = unit_model.get_chibi(support_pair.unit2)

    if unit1_chibi and unit2_chibi:
        combined_chibi = QImage(64, 32, QImage.Format_RGB32)
        painter = QPainter()
        painter.begin(combined_chibi)
        painter.drawImage(0, 0, unit1_chibi.toImage())
        painter.drawImage(32, 0, unit2_chibi.toImage())
        painter.end()
        combined_chibi = QPixmap.fromImage(combined_chibi)
        return combined_chibi
    return None

class SupportPairModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            support_pair = self._data[index.row()]
            text = support_pair.nid
            return text
        elif role == Qt.DecorationRole:
            support_pair = self._data[index.row()]
            pixmap = get_pixmap(support_pair)
            if pixmap:
                return QIcon(pixmap)
        return None

    def delete(self, idx):
        # Delete watchers
        # None needed -- Nothing else in editor/data uses support pairs 
        super().delete(idx)

    def on_nid_changed(self, old_value, new_value):
        pass

    def create_new(self):
        # Try to create a unique support pair
        for unit1 in DB.units:
            for unit2 in DB.units:
                new_support_pair = supports.SupportPair(
                    unit1.nid, unit2.nid, False, supports.SupportRankRequirementList())
                if new_support_pair.nid in DB.support_pairs.keys():
                    continue
                else:
                    return new_support_pair
        # If no unique support pair can be created, just fail silently
        return None
