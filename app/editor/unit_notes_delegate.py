from PyQt5.QtWidgets import QLineEdit, QItemDelegate

class UnitNotesDelegate(QItemDelegate):
    category_column = 0
    entries_column = 1

    def createEditor(self, parent, option, index):
        if index.column() == self.category_column:
            editor = QLineEdit(parent)
            return editor
        elif index.column() == self.entries_column:
            editor = QLineEdit(parent)
            return editor
        else:
            return super().createEditor(parent, option, index)