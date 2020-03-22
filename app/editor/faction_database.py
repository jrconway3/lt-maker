from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.resources import RESOURCES
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox

from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app.editor.icons import ItemIcon32
import app.editor.utilities as editor_utilities
from app import utilities

class FactionDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.factions
        title: str = 'Faction'
        right_frame = FactionProperties

        def deletion_func(view, idx):
            return view.model().rowCount() > 1 

        deletion_criteria = (deletion_func, "Cannot delete when only one faction left!")
        collection_model = FactionModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

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
        nid = name = utilities.get_next_name("New Faction", nids)
        DB.create_new_faction(nid, name)

class FactionProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.setStyleSheet("font: 10pt;")

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon32(self)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)
        self.name_box.edit.setMaxLength(13)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        top_section.addLayout(name_section)

        self.desc_box = PropertyBox("Description", QLineEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addWidget(self.desc_box)

        total_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        # Also change name if they are identical
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
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
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.desc_box.edit.setText(current.desc)
        self.icon_edit.set_current(current.icon_nid, current.icon_index)

# Testing
# Run "python -m app.editor.faction_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = FactionDatabase.create()
    window.show()
    app.exec_()
