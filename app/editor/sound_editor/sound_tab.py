from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, \
    QDialog, QAbstractItemView


from app.resources.resources import RESOURCES
from app.extensions.custom_gui import SFXTableView
from app.editor.data_editor import SingleResourceEditor, MultiResourceEditor
from app.editor.sound_editor.audio_widget import AudioWidget
from app.editor.sound_editor.sound_model import SFXModel, ProxyModel

class SFXTab(QWidget):
    def __init__(self, data, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.title = title

        self.setWindowTitle(self.title)
        self.setStyleSheet("font: 10pt;")

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setMinimumWidth(360)

        self.model = SFXModel(data, self)
        self.proxy_model = ProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.view = SFXTableView(None, self)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setModel(self.proxy_model)
        self.view.setSortingEnabled(True)
        self.view.clicked.connect(self.on_single_click)
        self.view.doubleClicked.connect(self.on_double_click)
        # Remove edit on double click
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.display = self.view

        self.audio_widget = AudioWidget(self)

        self.layout.addWidget(self.audio_widget)
        self.layout.addWidget(self.view)

        self.button = QPushButton("Add New SFX...")
        self.button.clicked.connect(self.append)
        self.layout.addWidget(self.button)

    def append(self):
        last_index = self.model.append()
        if last_index:
            self.view.setCurrentIndex(last_index)

    def reset(self):
        pass

    def get_selected(self):
        select = self.display.selectionModel()
        indices = select.selectedRows()
        return [self._data[self.proxy_model.mapToSource(index).row()] for index in indices]

    def on_single_click(self, index):
        selections = self.get_selected()
        if selections:
            sfx = selections[-1]
            # self.audio_widget.set_current(sfx)

    def on_double_click(self, index):
        selections = self.get_selected()
        if selections:
            sfx = selections[-1]
            self.audio_widget.set_current(sfx)
            self.audio_widget.play()

class SFXDatabase(SFXTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.sfx
        title = "SFX"

        dialog = cls(data, title, parent)
        return dialog

def get_sfx():
    window = SingleResourceEditor(SFXDatabase, ['sfx'])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_sfx = window.tab.get_selected()
        return selected_sfx, True
    else:
        return None, False

# Testing
# Run "python -m app.editor.sound_editor.sound_tab"
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    RESOURCES.load('default.ltproj')
    # DB.load('default.ltproj')
    # window = MultiResourceEditor((TileSetDatabase, TileMapDatabase), 
                                 # ("tilesets", "tilemaps"))
    window = SingleResourceEditor(SFXDatabase, ['sfx'])
    window.show()
    app.exec_()
