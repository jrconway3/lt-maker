from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QVBoxLayout, \
    QSpinBox
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.extensions.custom_gui import PropertyBox

from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app import utilities

class StatTypeDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.stats
        title: str = "Stat Types"
        right_frame = StatTypeProperties

        def deletion_func(view, idx):
            return view.window._data[idx].nid not in ("HP", "MOV")

        deletion_criteria = (deletion_func, "Cannot delete HP or MOV stats!")
        collection_model = StatTypeModel
        return cls(data, title, right_frame, deletion_criteria, collection_model, parent)

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

class StatTypeProperties(QWidget):
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
        self.name_box.edit.setMaxLength(13)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        self.max_box = PropertyBox("Maximum", QSpinBox, self)
        self.max_box.edit.setRange(0, 255)
        self.max_box.edit.setAlignment(Qt.AlignRight)
        self.max_box.edit.valueChanged.connect(self.maximum_changed)
        name_section.addWidget(self.max_box)

        self.desc_box = PropertyBox("Description", QLineEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)
        name_section.addWidget(self.desc_box)

        self.setLayout(name_section)
        name_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        # Also change name if they are identical
        if self.current.nid in ('MOV', 'HP') and text != self.current.nid:
            QMessageBox.warning(self.window, 'Warning', 'Cannot change ID of HP or MOV stat types')
            self.nid_box.edit.setText(self.current.nid)
            return
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
        self.current.nid = text
        self.window.update_list()

    def nid_change_watchers(self, old_nid, new_nid):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.change_key(old_nid, new_nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.change_key(old_nid, new_nid)

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Faction ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self.nid_change_watchers(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def desc_changed(self, text):
        self.current.desc = text

    def maximum_changed(self, val):
        self.current.maximum = val

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.max_box.edit.setValue(current.maximum)
        self.desc_box.edit.setText(current.desc)
