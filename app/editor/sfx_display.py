from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, QToolButton, \
    QLabel, QStyle, QVBoxLayout, QAbstractItemView
from PyQt5.QtCore import Qt, QDir, QSettings

import os

from app.data.resources import RESOURCES

from app.extensions.custom_gui import ResourceListView
from app.editor.base_database_gui import DatabaseTab, ResourceCollectionModel

from app import utilities

class SFXDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.sfx
        title = "Sound Effect"
        right_frame = SFXProperties
        collection_model = SFXModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent, button_text="Add New %s...", view_type=ResourceListView)
        return dialog

class SFXModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            sfx = self._data[index.row()]
            text = sfx.nid
            return text
        return None

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select SFX File", starting_path, "WAV Files (*.wav);;All FIles (*)")
        if ok:
            for fn in fns:
                if fn.endswith('.wav'):
                    nid = os.path.split(fn)[-1][:-4]
                    nid = utilities.get_next_name(nid, [d.nid for d in RESOURCES.sfx])
                    RESOURCES.create_new_sfx(nid, fn)
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Sound Effect must be in WAV format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

class SFXProperties(QWidget):
    def __init__(self, parent, current=None):
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window
        self.main_editor = self.resource_editor.window

        self.current = current

        self.playing: bool = False

        self.status_label = QLabel("Stopped")

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.loop_button = QToolButton(self)
        self.loop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaLoop))
        self.loop_button.clicked.connect(self.loop_clicked)
        self.loop_button.setCheckable(True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        hbox_layout = QHBoxLayout()
        hbox_layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        hbox_layout.addWidget(self.status_label)
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.loop_button)

        self.nid_label = QLabel("Nothing is here yet")
        self.nid_label.setStyleSheet("font-weight: bold")
        layout.addWidget(self.nid_label)
        layout.addLayout(hbox_layout)

        # Double-click vagaries
        view = self.window.left_frame.view
        view.doubleClicked.connect(self.on_double_click)
        view.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Remove edit on double click

    def on_double_click(self, index):
        new_sfx = RESOURCES.sfx[index.row()]
        self.set_current(new_sfx)
        self.play_sfx(self.current)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def set_current(self, current):
        self.stop_music()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.current = current
        self.nid_label.setText(self.current.nid)

    def play_clicked(self):
        if self.playing:
            self.stop_sfx()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.current:
            self.play_sfx(self.current)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def play_sfx(self, sfx):
        fn = sfx.full_path
        self.resource_editor.music_player.play_sfx(fn)
        self.playing = True
        self.status_label.setText("Playing")
        
    def stop_sfx(self):
        self.playing = False
        self.status_label.setText("Stopped")
        self.resource_editor.music_player.stop_sfx()
