from PyQt5.QtWidgets import QSpinBox, QItemDelegate

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import ComboBox, PropertyBox, DeletionDialog
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import MultiAttrListModel

from app.data.weapons import WeaponRank
from app.data import item_components

class WeaponRankMultiModel(MultiAttrListModel):
    def delete(self, idx):
        # Check to make sure nothing else is using this rank
        element = DB.weapon_ranks[idx]
        affected_weapons = [weapon for weapon in DB.weapons if 
                            any(adv.weapon_rank == element.rank for adv in weapon.rank_bonus) or
                            any(adv.weapon_rank == element.rank for adv in weapon.advantage) or 
                            any(adv.weapon_rank == element.rank for adv in weapon.disadvantage)]
        affected_items = item_components.get_items_using(item_components.Type.WeaponRank, element.rank, DB)
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
                item_components.swap_values(affected_items, item_components.Type.WeaponRank, element.rank, swap.rank)
                for weapon in affected_weapons:
                    weapon.rank_bonus.swap_rank(element.rank, swap.rank)
                    weapon.advantage.swap_rank(element.rank, swap.rank)
                    weapon.disadvantage.swap_rank(element.rank, swap.rank)
            else:
                return
        super().delete(idx)

    def create_new(self):
        nids = DB.weapon_ranks.keys()
        nid = str_utils.get_next_name("Rank", nids)
        new_weapon_rank = WeaponRank(nid, 1)
        DB.weapon_ranks.append(new_weapon_rank)
        return new_weapon_rank

    def change_watchers(self, data, attr, old_value, new_value):
        if attr == 'rank':
            self._data.update_nid(data, new_value)
            for weapon in DB.weapons:
                weapon.rank_bonus.swap_rank(old_value, new_value)
                weapon.advantage.swap_rank(old_value, new_value)
                weapon.disadvantage.swap_rank(old_value, new_value)
            affected_items = item_components.get_items_using(item_components.Type.WeaponRank, old_value, DB)
            item_components.swap_values(affected_items, item_components.Type.WeaponRank, old_value, new_value)

class RankDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model.rowCount() > 1

        return cls(DB.weapon_ranks, "Weapon Rank", 
                   ("rank", "requirement"),
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
