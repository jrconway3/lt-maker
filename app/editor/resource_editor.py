from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox
from PyQt5.QtCore import Qt

from collections import OrderedDict

from app.editor.icon_display import Icon16Display, Icon32Display, Icon80Display
from app.editor.portrait_display import PortraitDisplay
from app.editor.map_sprite_display import MapSpriteDisplay
from app.editor.panorama_display import PanoramaDisplay
from app.editor.map_display import MapDisplay
from app.editor.music_display import MusicDisplay

from app.data.resources import RESOURCES

from app.pygame_audio import PygameAudioPlayer

class ResourceEditor(QDialog):
    def __init__(self, parent=None, one_tab_only=None):
        super().__init__(parent)
        self.window = parent
        self.setWindowTitle("Resource Editor")
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.music_player = PygameAudioPlayer()
        self.music_player.setVolume(.5)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.tab_bar = QTabWidget(self)

        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)

        self.create_sub_widgets()
        for name, tab in self.tabs.items():
            self.tab_bar.addTab(tab, name)

        # Handle if only one tab is allowed
        if one_tab_only:
            for idx, name in enumerate(self.tabs.keys()):
                if name != one_tab_only:
                    self.tab_bar.setTabEnabled(idx, False)

        self.current_tab = self.tab_bar.currentWidget()
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Icons 16x16'] = Icon16Display.create(self)
        self.tabs['Icons 32x32'] = Icon32Display.create(self)
        self.tabs['Icons 80x72'] = Icon80Display.create(self)
        self.tabs['Portraits'] = PortraitDisplay.create(self)
        self.tabs['Panoramas'] = PanoramaDisplay.create(self)
        self.tabs['Map Sprites'] = MapSpriteDisplay.create(self)
        # self.tabs['Combat Animations'] = AnimationDisplay.create()
        # self.tabs['Combat Effects'] = CombatEffectDisplay.create()
        # self.tabs['Map Effects'] = MapEffectDisplay.create()
        self.tabs['Maps'] = MapDisplay.create(self)
        self.tabs['Music'] = MusicDisplay.create(self)
        # self.tabs['SFX'] = SFXDisplay.create()

    def on_tab_changed(self, index):
        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def accept(self):
        RESOURCES.serialize(self.window.current_proj)
        self.music_player.quit()
        super().accept()

    def reject(self):
        RESOURCES.reload()
        self.music_player.quit()
        super().reject()

    @staticmethod
    def get(parent, tab_name):
        dialog = ResourceEditor(parent, one_tab_only=tab_name)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            current_tab = dialog.current_tab
            selected_res = current_tab.right_frame.current
            return selected_res, True
        else:
            return None, False

# Testing
# Run "python -m app.editor.resource_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ResourceEditor()
    window.show()
    app.exec_()
