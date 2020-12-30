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
                for klass in affected_klasses:
                    klass.wexp_gain.get(swap.nid).absorb(klass.wexp_gain.get(nid))
                for unit in affected_units:
                    unit.wexp_gain.get(swap.nid).absorb(unit.wexp_gain.get(nid))
                item_components.swap_values(affected_items, components.Type.Equation, nid, swap.nid)
                for weapon in affected_weapons:
                    weapon.advantage.swap_type(nid, swap.nid)
                    weapon.disadvantage.swap_type(nid, swap.nid)
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
        nid = name = str_utils.get_next_name("New Weapon Type", nids)
        new_weapon = weapons.WeaponType(
            nid, name, weapons.CombatBonusList(),
            weapons.CombatBonusList(), weapons.CombatBonusList())
        DB.weapons.append(new_weapon)
        return new_weapon

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

    # Called on changing attribute
    def change_watchers(self, data, attr, old_value, new_value):
        pass
