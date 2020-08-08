from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QPushButton, \
    QMessageBox, QDialog, QSpinBox, QStyledItemDelegate, QVBoxLayout, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.data import Data
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data.weapons import AdvantageList

from app.extensions.custom_gui import ComboBox, PropertyBox, PropertyCheckBox, DeletionDialog
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_widgets import AppendMultiListWidget
from app.extensions.list_models import DragDropMultiAttrListModel

from app.editor.custom_widgets import WeaponTypeBox
from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app.editor.icons import ItemIcon16

from app import utilities
import app.editor.utilities as editor_utilities

class WeaponDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.weapons
        title = "Weapon Type"
        right_frame = WeaponProperties

        def deletion_func(model, index):
            return model._data[index].nid != "Default"

        collection_model = WeaponModel
        dialog = cls(data, title, right_frame, (deletion_func, None, deletion_func), collection_model, parent)
        return dialog

def get_pixmap(weapon):
    x, y = weapon.icon_index
    res = RESOURCES.icons16.get(weapon.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x*16, y*16, 16, 16)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class WeaponModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            weapon = self._data[index.row()]
            text = weapon.nid + " : " + weapon.name
            return text
        elif role == Qt.DecorationRole:
            weapon = self._data[index.row()]
            pixmap = get_pixmap(weapon)
            if pixmap:
                return QIcon(pixmap)
        return None

    def delete(self, idx):
        # Check to make sure nothing else is using me!!!
        weapon_type = self._data[idx]
        nid = weapon_type.nid
        affected_klasses = [klass for klass in DB.classes if klass.wexp_gain.get(nid).wexp_gain > 0]
        affected_units = [unit for unit in DB.units if unit.wexp_gain.get(nid).wexp_gain > 0]
        affected_items = [item for item in DB.items if item.weapon and item.weapon.value == nid]
        affected_weapons = [weapon for weapon in DB.weapons if weapon.advantage.contains(nid) or weapon.disadvantage.contains(nid)]
        if affected_klasses or affected_units or affected_items or affected_weapons:
            if affected_items:
                affected = Data(affected_items)
                from app.editor.item_database import ItemModel
                model = ItemModel
            elif affected_klasses:
                affected = Data(affected_klasses)
                from app.editor.class_database import ClassModel
                model = ClassModel
            elif affected_units:
                affected = Data(affected_units)
                from app.editor.unit_database import UnitModel
                model = UnitModel
            elif affected_weapons:
                affected = Data(affected_weapons)
                from app.editor.weapon_database import WeaponModel
                model = WeaponModel
            msg = "Deleting WeaponType <b>%s</b> would affect these objects." % nid
            swap, ok = DeletionDialog.get_swap(affected, model, msg, WeaponTypeBox(self.window, exclude=weapon_type), self.window)
            if ok:
                for klass in affected_klasses:
                    klass.wexp_gain.get(swap.nid).absorb(klass.wexp_gain.get(nid))
                for unit in affected_units:
                    unit.wexp_gain.get(swap.nid).absorb(unit.wexp_gain.get(nid))
                for item in affected_items:
                    item.weapon.value = swap.nid
                for weapon in affected_weapons:
                    weapon.advantage.swap(nid, swap.nid)
                    weapon.disadvantage.swap(nid, swap.nid)
            else:
                return  # User cancelled swap
        # Delete watchers
        for klass in DB.classes:
            klass.wexp_gain.remove_key(nid)
        for unit in DB.units:
            unit.wexp_gain.remove_key(nid)
        super().delete(idx)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New Weapon Type", nids)
        DB.create_new_weapon_type(nid, name)

    # Called on create_new, new, and duplicate
    # Makes sure that other datatypes that use this data, but not directly
    # are always updated correctly
    def update_watchers(self, idx):
        for klass in DB.classes:
            klass.wexp_gain.new(idx, DB.weapons)
        for unit in DB.units:
            unit.wexp_gain.new(idx, DB.weapons)

    # Called on drag and drop
    def update_drag_watchers(self, fro, to):
        for klass in DB.classes:
            klass.wexp_gain.move_index(fro, to)
        for unit in DB.units:
            unit.wexp_gain.move_index(fro, to)

class WeaponRankMultiModel(DragDropMultiAttrListModel):
    def delete(self, idx):
        # Check to make sure nothing else is using this rank
        element = DB.weapon_ranks[idx]
        affected_weapons = [weapon for weapon in DB.weapons if 
                            any(adv.weapon_rank == element.rank for adv in weapon.advantage) or 
                            any(adv.weapon_rank == element.rank for adv in weapon.disadvantage)]
        affected_items = [item for item in DB.items if item.level and item.level.value == element]
        if affected_weapons or affected_items:
            if affected_weapons:
                affected = Data(affected_weapons)
                from app.editor.weapon_database import WeaponModel
                model = WeaponModel
            elif affected_items:
                affected = Data(affected_items)
                from app.editor.item_database import ItemModel
                model = ItemModel
            msg = "Deleting WeaponRank <b>%s</b> would affect these objects." % element.rank
            combo_box = PropertyBox("Rank", ComboBox, self.window)
            objs = [rank for rank in DB.weapon_ranks if rank.rank != element.rank]
            combo_box.edit.addItems([rank.rank for rank in objs])
            obj_idx, ok = DeletionDialog.get_simple_swap(affected, model, msg, combo_box)
            if ok:
                swap = objs[obj_idx]
                for item in affected_items:
                    item.level.value = swap
                for weapon in affected_weapons:
                    weapon.advantage.swap_rank(element.rank, swap.rank)
                    weapon.disadvantage.swap_rank(element.rank, swap.rank)
            else:
                return
        super().delete(idx)

    def create_new(self):
        return self._data.add_new_default(DB)

    def change_watchers(self, data, attr, old_value, new_value):
        if attr == 'rank':
            self._data.update_nid(data, new_value)
            for weapon in DB.weapons:
                weapon.advantage.swap_rank(old_value, new_value)
                weapon.disadvantage.swap_rank(old_value, new_value)
            for item in DB.items:
                if item.level and item.level.value == old_value:
                    item.level.value = new_value

class RankDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model.rowCount() > 1

        return cls(DB.weapon_ranks, "Weapon Rank", 
                   ("rank", "requirement", "accuracy", "damage", "crit"),
                   WeaponRankMultiModel, (deletion_func, None, None))

class WeaponProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon16(self)
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

        self.magic_box = PropertyCheckBox("Magic", QCheckBox, self)
        self.magic_box.edit.stateChanged.connect(self.magic_changed)
        main_section.addWidget(self.magic_box)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        main_section.addSpacerItem(horiz_spacer)

        self.rank_button = QPushButton("Edit Weapon Ranks...")
        self.rank_button.clicked.connect(self.edit_weapon_ranks)
        main_section.addWidget(self.rank_button)

        attrs = ('weapon_type', 'weapon_rank', 'damage', 'resist', 'accuracy', 'avoid', 'crit', 'dodge', 'attack_speed', 'defense_speed')
        self.advantage = AppendMultiListWidget(AdvantageList(), "Advantage versus", attrs, AdvantageDelegate, self)
        self.disadvantage = AppendMultiListWidget(AdvantageList(), "Disadvantage versus", attrs, AdvantageDelegate, self)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addWidget(self.advantage)
        total_section.addWidget(self.disadvantage)

    def nid_changed(self, text):
        # Also change name if they are identical
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
        self.current.nid = text
        self.window.update_list()

    def nid_change_watchers(self, old_nid, new_nid):
        for klass in DB.classes:
            klass.wexp_gain.change_key(old_nid, new_nid)
        for unit in DB.units:
            unit.wexp_gain.change_key(old_nid, new_nid)
        for weapon in DB.weapons:
            weapon.advantage.swap(old_nid, new_nid)
            weapon.disadvantage.swap(old_nid, new_nid)
        for item in DB.items:
            if item.weapon and item.weapon.value == old_nid:
                item.weapon.value = new_nid
            elif item.spell and item.spell.value[0] == old_nid:
                item.spell.value = (new_nid, *item.spell.value[1:])

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Weapon Type ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self.nid_change_watchers(self._data.find_key(self.current), self.current.nid)
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
        self.magic_box.edit.setChecked(current.magic)
        self.advantage.set_current(current.advantage)
        self.disadvantage.set_current(current.disadvantage)
        self.icon_edit.set_current(current.icon_nid, current.icon_index)

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
                pixmap = get_pixmap(weapon_type)
                icon = QIcon(pixmap) if pixmap else None
                editor.addItem(icon, weapon_type.nid)
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
