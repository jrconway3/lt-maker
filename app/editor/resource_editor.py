from PyQt5.QtWidgets import QDialog, QGridLayout, QTabWidget, QDialogButtonBox, QSizePolicy
from PyQt5.QtCore import Qt, QSettings

from collections import OrderedDict

from app.editor.icon_display import Icon16Display, Icon32Display, Icon80Display
from app.editor.portrait_display import PortraitDisplay
from app.editor.map_sprite_display import MapSpriteDisplay
from app.editor.panorama_display import PanoramaDisplay
from app.editor.tile_display import TileSetDisplay, TileMapDisplay
from app.editor.animation_display import AnimationDisplay
from app.editor.combat_animation_display import CombatAnimDisplay
from app.editor.sfx_display import SFXDisplay
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
        self.music_player.set_volume(.5)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        # self.buttonbox.setFocusPolicy(Qt.NoFocus)

        # self.buttonbox = QHBoxLayout()
        # self.button_ok = QPushButton("Ok", self)
        # self.button_cancel = QPushButton("Cancel", self)
        # self.buttonbox.addWidget(self.button_ok)
        # self.buttonbox.addWidget(self.button_cancel)
        # self.button_ok.clicked.connect(self.accept)
        # self.button_cancel.clicked.connect(self.reject)
        # self.grid.addLayout(self.buttonbox, 1, 1)

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

    def keyPressEvent(self, event):
        key = event.key()
        # Don't have Enter close the entire resource editor
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def create_sub_widgets(self):
        self.tabs = OrderedDict()
        self.tabs['Icons 16x16'] = Icon16Display.create(self)
        self.tabs['Icons 32x32'] = Icon32Display.create(self)
        self.tabs['Icons 80x72'] = Icon80Display.create(self)
        self.tabs['Portraits'] = PortraitDisplay.create(self)
        self.tabs['Panoramas'] = PanoramaDisplay.create(self)
        self.tabs['Map Sprites'] = MapSpriteDisplay.create(self)
        self.tabs['Combat Anims'] = CombatAnimDisplay.create()
        # self.tabs['Combat Effects'] = CombatEffectDisplay.create()
        self.tabs['Map Animations'] = AnimationDisplay.create()
        self.tabs['Tilesets'] = TileSetDisplay.create(self)
        self.tabs['Tilemaps'] = TileMapDisplay.create(self)
        self.tabs['SFX'] = SFXDisplay.create(self)
        self.tabs['Music'] = MusicDisplay.create(self)

    def on_tab_changed(self, idx):
        # Make each tab individually resizable
        for i in range(self.tab_bar.count()):
            if i == idx:
                self.tab_bar.widget(i).setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                self.tab_bar.widget(i).setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def accept(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        RESOURCES.serialize(current_proj)
        self.music_player.quit()
        super().accept()

    def reject(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        RESOURCES.reload(current_proj)
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
