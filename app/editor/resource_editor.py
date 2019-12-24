from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox
from PyQt5.QtCore import Qt

from collections import OrderedDict

from app.editor.icon_display import Icon16Display, Icon32Display, Icon80Display
from app.editor.portrait_display import PortraitDisplay
from app.editor.map_sprite_display import MapSpriteDisplay
from app.editor.panorama_display import PanoramaDisplay

class ResourceEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resource Editor")
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.tab_bar = QTabWidget(self)

        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Icons 16x16'] = Icon16Display.create()
        self.tabs['Icons 32x32'] = Icon32Display.create()
        self.tabs['Icons 80x72'] = Icon80Display.create()
        self.tabs['Portraits'] = PortraitDisplay.create()
        self.tabs['Panoramas'] = PanoramaDisplay.create()
        self.tabs['Map Sprites'] = MapSpriteDisplay.create()
        # self.tabs['Combat Animations'] = AnimationDisplay.create()
        # self.tabs['Combat Effects'] = CombatEffectDisplay.create()
        # self.tabs['Map Effects'] = MapEffectDisplay.create()
        # self.tabs['Music'] = MusicDisplay.create()
        # self.tabs['SFX'] = SFXDisplay.create()

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def accept(self):
        super().accept()

    def reject(self):
        super().reject()

# Testing
# Run "python -m app.editor.resource_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ResourceEditor()
    window.show()
    app.exec_()
