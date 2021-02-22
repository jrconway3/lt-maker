from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.utilities.data import Data
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data import weapons, components, item_components

from app.editor.custom_widgets import WeaponTypeBox
from app.extensions.custom_gui import DeletionDialog
from app.editor.base_database_gui import DragDropCollectionModel

from app.utilities import str_utils
import app.editor.utilities as editor_utilities

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
        affected_items = item_components.get_items_using(components.Type.WeaponType, nid, DB)
        affected_weapons = [weapon for weapon in DB.weapons if weapon.advantage.contains(nid) or weapon.disadvantage.contains(nid)]
        if affected_klasses or affected_units or affected_items or affected_weapons:
            if affected_items:
                affected = Data(affected_items)
                from app.editor.item_editor.item_model import ItemModel
                model = ItemModel
            elif affected_klasses:
                affected = Data(affected_klasses)
                from app.editor.class_editor.class_model import ClassModel
                model = ClassModel
            elif affected_units:
                affected = Data(affected_units)
                from app.editor.unit_editor.unit_model import UnitModel
                model = UnitModel
            elif affected_weapons:
                affected = Data(affected_weapons)
                model = WeaponModel
            msg = "Deleting WeaponType <b>%s</b> would affect these objects." % nid
            swap, ok = DeletionDialog.get_swap(affected, model, msg, WeaponTypeBox(self.window, exclude=weapon_type), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return  # User cancelled swap
        # Delete watchers
        for klass in DB.classes:
            klass.wexp_gain.remove_key(nid)
        for unit in DB.units:
            unit.wexp_gain.remove_key(nid)
        super().delete(idx)

    def on_nid_changed(self, old_value, new_value):
        old_nid, new_nid = old_value, new_value
        for klass in DB.classes:
            klass.wexp_gain.change_key(old_nid, new_nid)
        for unit in DB.units:
            unit.wexp_gain.change_key(old_nid, new_nid)
        for weapon in DB.weapons:
            weapon.rank_bonus.swap_type(old_nid, new_nid)
            weapon.advantage.swap_type(old_nid, new_nid)
            weapon.disadvantage.swap_type(old_nid, new_nid)
        affected_items = item_components.get_items_using(components.Type.WeaponType, old_nid, DB)
        item_components.swap_values(affected_items, components.Type.WeaponType, old_nid, new_nid)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Weapon Type", nids)
        new_weapon = weapons.WeaponType(
            nid, name, weapons.CombatBonusList(),
            weapons.CombatBonusList(), weapons.CombatBonusList())
        DB.weapons.append(new_weapon)
        return new_weapon

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
            klass.wexp_gain.new(idx, DB.weapons)
        for unit in DB.units:
            unit.wexp_gain.new(idx, DB.weapons)

    def removeRows(self, row, count, parent) -> bool:
        result = super().removeRows(row, count, parent)
        if result and self.most_recent_dragdrop:
            fro, to = self.most_recent_dragdrop[0], self.most_recent_dragdrop[1]
            self._drag_foreign_data(fro, to)
        return result

    # Called on drag and drop
    def _drag_foreign_data(self, fro, to):
        for klass in DB.classes:
            klass.wexp_gain.move_index(fro, to)
        for unit in DB.units:
            unit.wexp_gain.move_index(fro, to)
