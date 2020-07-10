from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import Qt

from app.data.data import Data
from app.data.database import DB
from app.data.simple_unit_object import SimpleUnitObject

from app.parsers.equations import Parser

from app.extensions.custom_gui import DeletionDialog, PropertyBox, ComboBox
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import DragDropMultiAttrListModel

class EquationMultiModel(DragDropMultiAttrListModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() == 1 and role == Qt.DecorationRole:
            equation = self._data[index.row()]
            good = self.test_equation(equation)
            if good:
                icon = self.window.style().standardIcon(QStyle.SP_DialogApplyButton)
            else:
                icon = self.window.style().standardIcon(QStyle.SP_DialogCancelButton)
            return icon
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            data = self._data[index.row()]
            attr = self._headers[index.column()]
            return getattr(data, attr)
        return None

    def test_equation(self, equation) -> bool:
        try:
            parser = Parser(None)
            test_unit = SimpleUnitObject.from_prefab(DB.units[0], parser)
            result = parser.get(equation.nid, test_unit)
            result = parser.get_expression(equation.expression, test_unit)
            return True
        except Exception as e:
            print(e)
            return False

    def delete(self, idx):
        element = self._data[idx]
        affected_items = [item for item in DB.items if item.min_range == element.nid or item.max_range == element.nid]
        if affected_items:
            affected = Data(affected_items)
            from app.editor.item_database import ItemModel
            model = ItemModel
            msg = "Deleting Equation <b>%s</b> would affect these items" % element.nid
            combo_box = PropertyBox("Equation", ComboBox, self.window)
            objs = [eq for eq in DB.equations if eq.nid != element.nid]
            combo_box.edit.addItems([eq.nid for eq in objs])
            obj_idx, ok = DeletionDialog.get_simple_swap(affected, model, msg, combo_box)
            if ok:
                swap = objs[obj_idx]
                for item in affected_items:
                    if item.min_range == element.nid:
                        item.min_range = swap.nid
                    if item.max_range == element.nid:
                        item.max_range = swap.nid
            else:
                return
        super().delete(idx)

    def create_new(self):
        return self._data.add_new_default(DB)

    def change_watchers(self, data, attr, old_value, new_value):
        if attr == 'nid':
            self._data.update_nid(data, new_value)
            for item in DB.items:
                if item.min_range == old_value:
                    item.min_range = new_value
                if item.max_range == old_value:
                    item.max_range = new_value

class EquationDialog(MultiAttrListDialog):
    locked_vars = {"HIT", "AVOID", "CRIT_HIT", "CRIT_AVOID", 
                   "DAMAGE", "DEFENSE", "MAGIC_DAMAGE", "MAGIC_DEFENSE", 
                   "HITPOINTS", "MOVEMENT", "CRIT_ADD", "CRIT_MULT",
                   "DOUBLE_ATK", "DOUBLE_DEF", "STEAL_ATK", "STEAL_DEF", 
                   "HEAL", "RESCUE_AID", "RESCUE_WEIGHT", "RATING"}

    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model._data[index.row()].nid not in cls.locked_vars

        dlg = cls(DB.equations, "Equation", ("nid", "expression"), 
                  EquationMultiModel, (deletion_func, None, deletion_func), cls.locked_vars)
        return dlg
