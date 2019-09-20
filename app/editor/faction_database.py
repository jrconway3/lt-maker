from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app.editor.icons import ItemIcon32
from app import utilities

class FactionDatabase(DatabaseDialog):
    @classmethod
    def create(cls, parent=None):
        data = DB.factions
        title = 'Faction'
        right_frame = FactionProperties
        deletion_msg = "Cannot delete when only faction left!"
        creation_func = DB.create_new_faction
        collection_model = FactionModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model, parent)
        return dialog

class FactionModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            faction = self._data[index.row()]
            text = faction.nid + " : " + faction.name
            return text
        elif role == Qt.DecorationRole:
            faction = self._data[index.row()]
            x, y = faction.icon_index
            pixmap = QPixmap(faction.icon_fn).copy(x*32, y*32, 32, 32).scaled(64, 64)
            return QIcon(pixmap)
        return None

class FactionProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window

        grid = QGridLayout()
        self.setLayout(grid)

        self.current = current

        nid_label = QLabel('Unique ID: ')
        self.nid_edit = QLineEdit(self)
        self.nid_edit.setMaxLength(12)
        self.nid_edit.textChanged.connect(self.nid_changed)
        self.nid_edit.editingFinished.connect(self.nid_done_editing)
        grid.addWidget(nid_label, 0, 2)
        grid.addWidget(self.nid_edit, 0, 3)

        name_label = QLabel('Display Name: ')
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(12)
        self.name_edit.textChanged.connect(self.name_changed)
        grid.addWidget(name_label, 1, 2)
        grid.addWidget(self.name_edit, 1, 3)

        desc_label = QLabel("Description: ")
        self.desc_edit = QLineEdit(self)
        self.desc_edit.textChanged.connect(self.desc_changed)
        grid.addWidget(desc_label, 2, 0)
        grid.addWidget(self.desc_edit, 2, 1, 1, 3)

        self.icon_edit = ItemIcon32(None, self)
        grid.addWidget(self.icon_edit, 0, 0, 2, 2)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Faction ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def desc_changed(self, text):
        self.current.desc = text

    def set_current(self, current):
        self.current = current
        self.nid_edit.setText(current.nid)
        self.name_edit.setText(current.name)
        self.desc_edit.setText(current.desc)
        self.icon_edit.set_current(current.icon_fn, current.icon_index)

# Testing
# Run "python -m app.editor.faction_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = FactionDatabase.create()
    window.show()
    app.exec_()
