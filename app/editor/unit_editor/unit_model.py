from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data import units, weapons, stats
from app.data.level_units import UniqueUnit

from app.extensions.custom_gui import DeletionDialog

from app.editor.custom_widgets import UnitBox
from app.editor.base_database_gui import DragDropCollectionModel
import app.editor.utilities as editor_utilities
from app.utilities import str_utils

def get_chibi(unit):
    res = RESOURCES.portraits.get(unit.portrait_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(96, 16, 32, 32)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class UnitModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit = self._data[index.row()]
            text = unit.nid
            return text
        elif role == Qt.DecorationRole:
            unit = self._data[index.row()]
            # Get chibi image
            pixmap = get_chibi(unit)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        return None

    def delete(self, idx):
        # check to make sure nothing else is using me!!!
        unit = self._data[idx]
        nid = unit.nid
        affected_ais = [ai for ai in DB.ai if ai.has_unit_spec("ID", nid)]
        affected_levels = [level for level in DB.levels if any(isinstance(unit, UniqueUnit) and unit.nid == nid for unit in level.units)]
        if affected_ais:
            from app.editor.ai_editor.ai_model import AIModel
            model = AIModel
        elif affected_levels:
            from app.editor.global_editor.level_menu import LevelModel
            model = LevelModel
            msg = "Deleting Unit <b>%s</b> would affect these objects" % nid
            swap, ok = DeletionDialog.get_swap(affected_ais, model, msg, UnitBox(self.window, exclude=unit), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        for ai in DB.ai:
            ai.change_unit_spec("ID", old_nid, new_nid)
        for level in DB.levels:
            for unit in level.units:
                if isinstance(unit, UniqueUnit) and unit.nid == old_nid:
                    unit.nid = new_nid
            for unit_group in level.unit_groups:
                unit_group.swap(unit.nid, new_nid)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Unit", nids)
        bases = {k: 0 for k in DB.stats.keys()}
        growths = {k: 0 for k in DB.stats.keys()}
        wexp_gain = {weapon_nid: DB.weapons.default() for weapon_nid in DB.weapons.keys()}
        new_unit = units.UnitPrefab(nid, name, '', None, 1, DB.classes[0].nid, [],
                                    bases, growths, [], [], wexp_gain)
        DB.units.append(new_unit)
        return new_unit
