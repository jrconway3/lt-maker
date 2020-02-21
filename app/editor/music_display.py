from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, QToolButton, \
    QLabel, QStyle, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt, QDir

import os

from app.data.resources import RESOURCES

from app.extensions.custom_gui import give_timer
from app.editor.base_database_gui import DatabaseTab, CollectionModel

import app.data.constants as constants

class MusicDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.music
        title = "Song"
        right_frame = MusicProperties
        collection_model = MusicModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...")
        return dialog

    def create_new(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self, "Select Music File", starting_path, "OGG Files (*.ogg);;All FIles (*)")
        if ok:
            if fn.endswith('.ogg'):
                full_path = fn
                local_name = os.path.split(fn)[-1]
                nid = local_name[:-4]
                RESOURCES.create_new_music(nid, full_path)
                self.after_new()
            else:
                QMessageBox.critical(self.window, "File Type Error!", "Music must be in OGG format!")

    def save(self):
        return None

class MusicModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            music = self._data[index.row()]
            text = music.nid
            return text
        return None

class MusicProperties(QWidget):
    default_text = "Nothing Playing"
    playing_text = "%s"

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window
        self.main_editor = self.resource_editor.window

        # Music Properties is set up different than most resource tabs
        # Music Properties ALWAYS shows the currently playing song
        # TODO: Need to add Double Click on a song to play it

        give_timer(self, constants.FPS)

        self.current = current

        self.currently_playing = None

        self.currently_playing_label = QLabel(self.default_text)

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.stop_button = QToolButton(self)
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop_clicked)
        self.stop_button.setEnabled(False)

        self.time_slider = QSlider(Qt.Horizontal, self)
        self.time_slider.setRange(0, 1)
        self.time_slider.setValue(0)
        self.time_slider.sliderPressed.connect(self.slider_pressed)
        self.time_slider.sliderReleased.connect(self.slider_released)

        self.time_label = QLabel("00:00 / 00:00")
        self.duration = 0

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        hbox_layout = QHBoxLayout()
        hbox_layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        hbox_layout.addWidget(self.currently_playing_label)
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)

        title_label = QLabel("Currently Playing")
        title_label.setStyleSheet("font-weight: bold")
        layout.addWidget(title_label)
        layout.addLayout(hbox_layout)

        time_layout = QHBoxLayout()
        time_layout.setAlignment(Qt.AlignTop)

        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.time_label)

        layout.addLayout(time_layout)

    def tick(self):
        if self.currently_playing:
            val = self.resource_editor.music_player.get_position()
            self.duration = self.resource_editor.music_player.duration
            val %= self.duration
            self.time_slider.setValue(val)
            minutes = int(val / 1000 / 60)
            seconds = int(val / 1000 % 60)
            thru_song = "%02d:%02d" % (minutes, seconds)
            minutes = int(self.duration / 1000 / 60)
            seconds = int(self.duration / 1000 % 60)
            song_length = "%02d:%02d" % (minutes, seconds)
            self.time_label.setText(thru_song + " / " + song_length)
        else:
            self.time_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")

    def set_current(self, current):
        self.current = current

    def slider_pressed(self):
        self.resource_editor.music_player.pause()

    def slider_released(self):
        self.resource_editor.music_player.set_position(self.time_slider.value())
        self.resource_editor.music_player.unpause()

    def play_clicked(self):
        if self.currently_playing:
            self.pause_music()
            self.stop_button.setEnabled(False)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.current:
            self.play_music(self.current.nid)
            self.stop_button.setEnabled(True)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def stop_clicked(self):
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.stop_button.setEnabled(False)
        self.stop_music()

    def play_music(self, nid):
        music_resource = self._data.get(nid)
        print(music_resource.full_path)
        fn = music_resource.full_path

        new_song = self.resource_editor.music_player.play(fn)

        if new_song:
            self.time_slider.setRange(0, self.resource_editor.music_player.duration)
            print(self.time_slider.maximum())
            self.time_slider.setValue(0)
        
        self.currently_playing = nid
        self.currently_playing_label.setText(self.playing_text % nid)

    def pause_music(self):
        self.currently_playing = None
        self.resource_editor.music_player.pause()
        
    def stop_music(self):
        self.currently_playing = None
        self.currently_playing_label.setText(self.default_text)
        self.resource_editor.music_player.stop()
