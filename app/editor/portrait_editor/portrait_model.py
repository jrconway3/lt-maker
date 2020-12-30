import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

from app.resources.portraits import Portrait
from app.resources.resources import RESOURCES

from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog
from app.editor.base_database_gui import ResourceCollectionModel
from app.editor.settings import MainSettingsController
from app.utilities import str_utils
import app.editor.utilities as editor_utilities

class PortraitModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            portrait = self._data[index.row()]
            text = portrait.nid
            return text
        elif role == Qt.DecorationRole:
            portrait = self._data[index.row()]
            if not portrait.pixmap:
                portrait.pixmap = QPixmap(portrait.full_path)
            pixmap = portrait.pixmap
            chibi = pixmap.copy(96, 16, 32, 32)
            chibi = QPixmap.fromImage(editor_utilities.convert_colorkey(chibi.toImage()))
            return QIcon(chibi)
        return None

    def create_new(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Portriats", starting_path, "PNG Files (*.png);;All Files(*)")
        new_portrait = None
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]
                    pix = QPixmap(fn)
                    nid = str_utils.get_next_name(nid, [d.nid for d in RESOURCES.portraits])
                    if pix.width() == 128 and pix.height() == 112:
                        new_portrait = Portrait(nid, fn, pix)
                        RESOURCES.portraits.append(new_portrait)
                    else:
                        QMessageBox.critical(self.window, "Error", "Image is not correct size (128x112 px)")
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Portrait must be PNG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.set_last_open_path(parent_dir)
        return new_portrait

    def delete(self, idx):
        # Check to see what is using me?
        res = self._data[idx]
        nid = res.nid
        affected_units = [unit for unit in DB.units if unit.portrait_nid == nid]
        if affected_units:
            affected = Data(affected_units)
            from app.editor.unit_database import UnitModel
            model = UnitModel
            msg = "Deleting Portrait <b>%s</b> would affect these units."
            ok = DeletionDialog.inform(affected, model, msg, self.window)
            if ok:
                pass
            else:
                return
        super().delete(idx)

    def nid_change_watchers(self, portrait, old_nid, new_nid):
        # What uses portraits
        # Units (Later Dialogues)
        for unit in DB.units:
            if unit.portrait_nid == old_nid:
                unit.portrait_nid = new_nid
