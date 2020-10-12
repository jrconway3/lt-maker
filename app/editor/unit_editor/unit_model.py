from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data import units, weapons, stats

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
        affected_ais = [ai for ai in DB.ai if 
                        any(behaviour.target_spec and 
                        behaviour.target_spec[0] == "Unit" and 
                        behaviour.target_spec[1] == nid 
                        for behaviour in ai.behaviours)]
        if affected_ais:
            from app.editor.ai_database import AIModel
            model = AIModel
            msg = "Deleting Unit <b>%s</b> would affect these ais" % nid
            swap, ok = DeletionDialog.get_swap(affected_ais, model, msg, UnitBox(self.window, exclude=unit), self.window)
            if ok:
                self.change_nid(nid, swap.nid)
            else:
                return
        # TODO this should be done at the closing of the unit editor
        # for level in DB.levels:
        #   level.units = [unit for unit in level.units if nid != unit.nid]
        super().delete(idx)

    def change_nid(self, old_nid, new_nid):
        for ai in DB.ai:
            for behaviour in ai.behaviours:
                if behaviour.target_spec and behaviour.target_spec[0] == "Unit" and behaviour.target_spec[1] == old_nid:
                    behaviour.target_spec[1] = new_nid

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Unit", nids)
        bases = stats.StatList.default(DB)
        growths = stats.StatList.default(DB)
        wexp_gain = weapons.WexpGainList.default(DB)
        new_unit = units.UnitPrefab(nid, name, '', None, 1, DB.classes[0].nid, [],
                                    bases, growths, [], [], wexp_gain)
        DB.units.append(new_unit)
        return new_unit
