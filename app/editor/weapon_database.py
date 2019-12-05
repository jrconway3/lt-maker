from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QLineEdit, QPushButton, \
    QMessageBox, QDialog, QSpinBox, QStyledItemDelegate, QVBoxLayout, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.database import DB
from app.data.weapons import AdvantageList

from app.editor.custom_gui import ComboBox, PropertyBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.misc_dialogs import RankDialog
from app.editor.sub_list_widget import AppendMultiListWidget
from app.editor.icons import ItemIcon16
from app import utilities

class WeaponDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.weapons
        title = "Weapon Type"
        right_frame = WeaponProperties

        def deletion_func(view, idx):
            return view.window._data[idx].nid != "Default"

        deletion_criteria = (deletion_func, "Cannot delete Default weapon type!")
        collection_model = WeaponModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New " + self.title, nids)
        DB.create_new_weapon_type(nid, name)
        self.after_new()

class WeaponModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            weapon = self._data[index.row()]
            text = weapon.nid + " : " + weapon.name
            return text
        elif role == Qt.DecorationRole:
            weapon = self._data[index.row()]
            x, y = weapon.icon_index
            pixmap = QPixmap(weapon.icon_fn).copy(x*16, y*16, 16, 16).scaled(64, 64)
            return QIcon(pixmap)
        return None

class WeaponProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon16(None, self)
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

        main_section = QHBoxLayout()

        magic_section = QHBoxLayout()
        magic_label = QLabel("Magic")
        magic_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.magic_box = QCheckBox(self)
        self.magic_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.magic_box.stateChanged.connect(self.magic_changed)
        magic_section.addWidget(self.magic_box)
        magic_section.addWidget(magic_label)
        magic_section.setAlignment(magic_label, Qt.AlignLeft)
        main_section.addLayout(magic_section)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        main_section.addSpacerItem(horiz_spacer)

        self.rank_button = QPushButton("Edit Weapon Ranks...")
        self.rank_button.clicked.connect(self.edit_weapon_ranks)
        main_section.addWidget(self.rank_button)

        attrs = ('weapon_type', 'weapon_rank', 'damage', 'resist', 'accuracy', 'avoid', 'crit', 'dodge', 'attackspeed')
        self.advantage = AppendMultiListWidget(AdvantageList(), "Advantage versus", attrs, AdvantageDelegate, self)
        self.disadvantage = AppendMultiListWidget(AdvantageList(), "Disadvantage versus", attrs, AdvantageDelegate, self)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addWidget(self.advantage)
        total_section.addWidget(self.disadvantage)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Weapon Type ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def magic_changed(self, state):
        self.current.magic = bool(state)

    def edit_weapon_ranks(self):
        dlg = RankDialog.create()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            # Need to modify current weapon ranks here
            # for weapon in DB.weapons:
                # for advantage in weapon.advantage:
            pass
        else:
            pass

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.magic_box.setChecked(current.magic)
        self.advantage.set_current(current.advantage)
        self.disadvantage.set_current(current.disadvantage)
        self.icon_edit.set_current(current.icon_fn, current.icon_index)

class AdvantageDelegate(QStyledItemDelegate):
    type_column = 0
    rank_column = 1
    int_columns = (2, 3, 4, 5, 6, 7, 8)

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setRange(-255, 255)
            return editor
        elif index.column() == self.rank_column:
            editor = ComboBox(parent)
            for rank in DB.weapon_ranks:
                editor.addItem(rank.rank)
            editor.addItem("All")
            return editor
        elif index.column() == self.type_column:
            editor = ComboBox(parent)
            for weapon_type in DB.weapons:
                x, y = weapon_type.icon_index
                icon = QPixmap(weapon_type.icon_fn).copy(x*16, y*16, 16, 16)
                editor.addItem(QIcon(icon), weapon_type.nid)
            return editor
        else:
            return super().createEditor(parent, option, index)

class WexpGainDelegate(QItemDelegate):
    bool_column = 0
    weapon_type_column = 1
    int_column = 2

    def createEditor(self, parent, option, index):
        if index.column() == self.int_column:
            editor = QSpinBox(parent)
            editor.setRange(0, 999)
            return editor
        else:
            return None

# Testing
# Run "python -m app.editor.weapon_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = WeaponDatabase.create()
    window.show()
    app.exec_()
