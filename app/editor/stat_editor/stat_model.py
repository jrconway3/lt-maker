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
        # All classes and units are automatically effected
        # We will just let equations check themselves!!!
        # Also some item component can use stat lists???
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.remove_key(nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.remove_key(nid)
        super().delete(idx)

    # Called on create_new, new, and duplicate
    # Makes sure that other datatypes that use this dat, but not directly
    # Are always updated correctly
    def update_watchers(self, idx):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.new_key(DB.stats[idx].nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.new_key(DB.stats[idx].nid)

    # Called on drag and drop
    def update_drag_watchers(self, fro, to):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.move_index(fro, to)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.move_index(fro, to)
