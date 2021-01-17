from PyQt5.QtCore import Qt

from app.data.database import DB
from app.editor.base_database_gui import DragDropCollectionModel

class StatTypeModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            stat_type = self._data[index.row()]
            text = stat_type.nid + ": " + stat_type.name
            return text
        return None

    def create_new(self):
        return self._data.add_new_default(DB)

    # Called on delete
    def delete(self, idx):
        # Check to make sure nothing else is using me!!!
        stat_type = self._data[idx]
        nid = stat_type.nid
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.remove_key(nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.remove_key(nid)
        super().delete(idx)

    def append(self):
        last_index = super().append()
        if last_index:
            idx = last_index.row()
            self._update_foreign_data(idx)

    def new(self, idx):
        new_index = super().new(idx)
        if new_index:
            idx = new_index.row()
            self._update_foreign_data(idx)

    def duplicate(self, idx):
        new_index = super().duplicate(idx)
        if new_index:
            idx = new_index.row()
            self._update_foreign_data(idx)

    def _update_foreign_data(self, idx):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.new_key(idx, DB.stats[idx].nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.new_key(idx, DB.stats[idx].nid)

    def removeRows(self, row, count, parent):
        result = super().removeRows(row, count, parent)
        if result and self.most_recent_dragdrop:
            fro, to = self.most_recent_dragdrop[0], self.most_recent_dragdrop[1]
            self._drag_foreign_data(fro, to)

    # Called on drag and drop
    def _drag_foreign_data(self, fro, to):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.move_index(fro, to)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.move_index(fro, to)
