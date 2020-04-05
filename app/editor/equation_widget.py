from app.data.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog, PropertyBox, ComboBox
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import DragDropMultiAttrListModel

class EquationMultiModel(DragDropMultiAttrListModel):
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
    locked_vars = {"ATTACKSPEED", "HIT", "AVOID", "CRIT_HIT", "CRIT_AVOID", 
                   "DAMAGE", "DEFENSE", "MAGIC_DAMAGE", "MAGIC_DEFENSE", 
                   "CRIT_ADD", "CRIT_MULT",
                   "DOUBLE_ATK", "DOUBLE_DEF", "STEAL_ATK", "STEAL_DEF", 
                   "HEAL", "RESCUE_AID", "RESCUE_WEIGHT", "RATING"}

    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model._data[index.row()].nid not in cls.locked_vars

        dlg = cls(DB.equations, "Equation", ("nid", "expression"), 
                  EquationMultiModel, (deletion_func, None, deletion_func), cls.locked_vars)
        return dlg
