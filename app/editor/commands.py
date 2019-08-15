from PyQt5.QtWidgets import QUndoCommand
from PyQt5.QtCore import QItemSelectionModel

from app.data.level import Level

class CreateNewLevel(QUndoCommand):
    def __init__(self, title, nid, level_menu):
        self.new_level = Level(nid, title)
        self.level_menu = level_menu
        self.old_idx = level_menu.model.rowCount()
        super().__init__("Creating level %s: %s" % (nid, title))

    def undo(self):
        self.old_idx = self.level_menu.model.get_index_from_item(self.new_level)
        self.level_menu.model.remove(self.old_idx, self.new_level)

    def redo(self):
        model_index = self.level_menu.model.insert(self.old_idx, self.new_level)
        self.level_menu.listview.selectionModel().setCurrentIndex(model_index, QItemSelectionModel.NoUpdate)
