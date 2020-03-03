from app.data.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog
from app.extensions.list_dialogs import SingleListDialog, MultiAttrListDialog

class TagDialog(SingleListDialog):
    @classmethod
    def create(cls):
        return cls(DB.tags, "Tag")

    def accept(self):
        for action in self.actions:
            kind = action[0]
            if kind == 'Delete':
                self.on_delete(action[1])
            elif kind == 'Change':
                self.on_change(*action[1:])
            elif kind == 'Append':
                self.on_change(action[1])
        super().accept()

    def on_delete(self, element):
        for klass in DB.classes:
            if element in klass.tags:
                klass.tags.remove(element)

    def on_change(self, old, new):
        for klass in DB.classes:
            if old in klass.tags:
                klass.tags.remove(old)
                klass.tags.append(new)

    def on_append(self, element):
        pass
