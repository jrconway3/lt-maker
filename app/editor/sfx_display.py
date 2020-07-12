from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, QToolButton, \
    QLabel, QStyle, QVBoxLayout, QAbstractItemView, QLineEdit
from PyQt5.QtCore import Qt, QDir, QSettings

import os

from app.resources.sounds import SFX
from app.resources.resources import RESOURCES

from app.extensions.custom_gui import PropertyBox, ResourceMultiselectListView
from app.editor.timer import TIMER
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

        dialog = cls(data, title, right_frame, deletion_criteria, 
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceMultiselectListView)
        return dialog

class SFXModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        item = self._data[index.row()]
        if role == Qt.DisplayRole:
            if item.tag:
                return item.nid + " (%s)" % item.tag
            else:
                return item.nid
        return None

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select SFX File", starting_path, "OGG Files (*.ogg);;All FIles (*)")
        if ok:
            for fn in fns:
                if fn.endswith('.ogg'):
                    nid = os.path.split(fn)[-1][:-4]
                    nid = utilities.get_next_name(nid, [d.nid for d in RESOURCES.sfx])
                    new_sfx = SFX(nid, fn)
                    RESOURCES.sfx.append(new_sfx)
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Sound Effect must be in OGG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

class SFXProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window
        self.main_editor = self.resource_editor.window

        self.current = current

        self.playing: bool = False
        self.loop: bool = False

        self.start_time = 0
        self.duration = 0

        self.status_label = QLabel("Stopped")

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.loop_button = QToolButton(self)
        self.loop_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
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

        self.tag_box = PropertyBox("Tag", QLineEdit, self)
        self.tag_box.edit.setPlaceholderText("Untagged")
        self.tag_box.edit.textEdited.connect(self.tag_changed)
        layout.addWidget(self.tag_box)

        # Double-click vagaries
        self.view = self.window.left_frame.view
        self.view.doubleClicked.connect(self.on_double_click)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Remove edit on double click

        TIMER.tick_elapsed.connect(self.tick)

    def tick(self):
        if self.playing:
            if self.duration != 0 and (self.resource_editor.music_player.get_time() - self.start_time > self.duration):
                # Stop the song now
                self.duration = 0
                self.play_clicked()

    def on_double_click(self, index):
        new_sfx = index.internalPointer()
        self.set_current(new_sfx)
        if self.current:
            self.start_time = self.resource_editor.music_player.get_time()
            self.duration = self.play_sfx(self.current)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def tag_changed(self, text):
        print("tag changed")
        print(text, flush=True)
        # Can change multiple tags at the same time
        indices = self.view.selectionModel().selectedIndexes()
        if len(indices) > 1:
            for index in indices:
                self._data[index.row()].tag = text
            # self.view.model().dataChanged.emit(indices[0], indices[-1])
            self.view.model().layoutChanged.emit()
        else:
            self.current.tag = text
            # self.view.model().
            self.view.model().layoutChanged.emit()

    def set_current(self, current):
        self.stop_sfx()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        if current in RESOURCES.sfx:
            self.current = current
            self.nid_label.setText(self.current.nid)
            if self.current.tag:
                self.tag_box.edit.setText(self.current.tag)
            else:
                self.tag_box.edit.setText('')
            self.play_button.setEnabled(True)
            self.loop_button.setEnabled(True)

    def play_clicked(self):
        if self.playing:
            self.stop_sfx()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.current:
            self.play_sfx(self.current)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def loop_clicked(self, val):
        if val:
            self.loop = True
        else:
            self.loop = False

    def play_sfx(self, sfx):
        fn = sfx.full_path
        self.resource_editor.music_player.play_sfx(fn, self.loop)
        self.playing = True
        self.status_label.setText("Playing")
        
    def stop_sfx(self):
        self.playing = False
        self.status_label.setText("Stopped")
        self.resource_editor.music_player.stop_sfx()
