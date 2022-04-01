from app.data.database import DB

from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import MultiAttrListModel

class GameVarSlotMultiModel(MultiAttrListModel):
    def create_new(self):
        return self._data.add_new_default(DB)

    def on_attr_changed(self, data, attr, old_value, new_value):
        if attr == 'nid':
            DB.game_var_slots.update_nid(data, new_value)

class GameVarSlotDialog(MultiAttrListDialog):
    @classmethod
    def create(cls, parent=None):
        def deletion_func(model, index):
            return True
        dlg = cls(DB.game_var_slots, "Game Var Slots", ("nid", "desc"), GameVarSlotMultiModel, (deletion_func, None, deletion_func), [], parent)
        return dlg

# Testing
# Run "python -m app.editor.tag_widget"
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    DB.load('default.ltproj')
    window = GameVarSlotDialog.create()
    window.show()
    app.exec_()
