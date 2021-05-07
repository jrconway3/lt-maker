from PyQt5.QtCore import Qt

from app.utilities.data import Data
from app.data.database import DB
from app.resources import combat_anims

from app.editor.base_database_gui import ResourceCollectionModel

from app.extensions.custom_gui import DeletionDialog

from app import utilities

class CombatAnimModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            animation = self._data[index.row()]
            text = animation.nid
            return text
        elif role == Qt.DecorationRole:
            # TODO create icon out of standing image
            return None
        return None

    def create_new(self):
        nid = utilities.get_next_name('New Combat Anim', self._data.keys())
        new_anim = combat_anims.CombatAnimation(nid)
        self._data.append(new_anim)
        return new_anim

    def delete(self, idx):
        # Check to see what is using me?
        res = self._data[idx]
        nid = res.nid
        affected_classes = [klass for klass in DB.classes if klass.combat_anim_nid == nid]

        if affected_classes:
            affected = Data(affected_classes)
            from app.editor.class_editor.class_model import ClassModel
            model = ClassModel
            msg = "Deleting Combat Animation <b>%s</b> would affect these classes"
            ok = DeletionDialog.inform(affected, model, msg, self.window)
            if ok:
                for klass in affected_classes:
                    klass.combat_anim_nid = None
            else:
                return
        super().delete(idx)
