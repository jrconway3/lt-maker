from PyQt5.QtWidgets import QLineEdit, QItemDelegate

from app.extensions.list_models import DoubleListModel

class ClassFieldDelegate(QItemDelegate):
    key_col = 0
    val_col = 1

    def createEditor(self, parent, option, index):
        if index.column() == self.key_col:
            editor = QLineEdit(parent)
            return editor
        elif index.column() == self.val_col:
            editor = QLineEdit(parent)
            return editor
        else:
            return super().createEditor(parent, option, index)

class ClassFieldDoubleListModel(DoubleListModel):
    """
    Handles a simple list of 2-tuples/lists where
    both values are strings that can be edited
    """
    def create_new(self):
        new_category = "New Key"
        new_entry = "New Value"
        self._data.append([new_category, new_entry])
