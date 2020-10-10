from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QPushButton, \
    QMessageBox, QDialog, QSpinBox, QStyledItemDelegate, QVBoxLayout, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.utilities.data import Data
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data.weapons import CombatBonusList

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
    if not res.image:
        res.image = QPixmap(res.full_path)
    pixmap = res.image.copy(x*16, y*16, 16, 16)
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
