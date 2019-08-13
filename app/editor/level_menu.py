from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QDialog

from app.editor.custom_gui import SignalList
from app.editor.new_level_dialog import NewLevelDialog

class LevelMenu(QWidget):
    def __init__(self, window=None):
        super().__init__(window)
        self.main_editor = window

        self.grid = QGridLayout()

        self.list = SignalList(self)
        self.list.setMinimumSize(128, 320)
        self.list.uniformItemSizes = True

        self.button = QPushButton("Create New Level...")
        self.button.clicked.connect(self.create_new_level_dialog)

        self.grid.addWidget(self.list, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

    def create_new_level_dialog(self):
        dialog = NewLevelDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_level_command = dialog.get_command()
            self.main_editor.undo_stack.push(new_level_command)
            self.main_editor.map_view.update_view()
