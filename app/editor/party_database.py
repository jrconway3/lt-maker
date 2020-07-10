from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QVBoxLayout
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, DeletionDialog
from app.editor.custom_widgets import UnitBox, PartyBox
from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app import utilities

class PartyDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.parties
        title: str = "Parties"
        right_frame = PartyProperties

        collection_model = PartyModel
        return cls(data, title, right_frame, None, collection_model, parent)

class PartyModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            party = self._data[index.row()]
            text = party.nid + ": " + party.name
            return text
        return None

    def create_new(self):
        return self._data.add_new_default(DB)

    def delete(self, idx):
        party = self._data[idx]
        nid = party.nid
        affected_levels = [level for level in DB.levels if level.party == nid]
        if affected_levels:
            from app.editor.level_menu import LevelModel
            model = LevelModel
            msg = "Deleting Party <b>%s</b> would affect this level" % nid
            swap, ok = DeletionDialog.get_swap(affected_levels, model, msg, PartyBox(self.window, exclude=party), self.window)
            if ok:
                self.change_nid(nid, swap.nid)
            else:
                return
            super().delete(idx)

    def change_nid(self, old_nid, new_nid):
        # Levels can be effected
        for level in DB.levels:
            if level.party == old_nid:
                level.party = new_nid

class PartyProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)
        self.name_box.edit.setMaxLength(20)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        self.leader_box = UnitBox(self, title="Leader Unit")
        self.leader_box.edit.currentIndexChanged.connect(self.leader_changed)
        name_section.addWidget(self.leader_box)

        self.setLayout(name_section)
        name_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
        self.current.nid = text
        self.window.update_list()

    def nid_change_watchers(self, old_nid, new_nid):
        self.window.model.change_nid(old_nid, new_nid)

    def nid_done_editing(self):
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Party ID %s already in use' % self.current.nid)
        self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self.nid_change_watchers(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def leader_changed(self, idx):
        self.current.leader = DB.units[idx].nid

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.leader_box.edit.setValue(current.leader)
