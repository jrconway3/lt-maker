from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, QToolButton, \
    QLabel, QStyle, QVBoxLayout, QSlider, QAbstractItemView, QCheckBox, QPushButton
from PyQt5.QtCore import Qt, QDir, QSettings

import os

from app.resources.sounds import Song
from app.resources.resources import RESOURCES

from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import ResourceListView, DeletionDialog
from app.editor.timer import TIMER
from app.editor.base_database_gui import DatabaseTab, ResourceCollectionModel

from app import utilities

class MusicDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.music
        title = "Song"
        right_frame = MusicProperties
        collection_model = MusicModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceListView)
        return dialog

class MusicModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            music = self._data[index.row()]
            text = music.nid
            return text
        return None

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Music File", starting_path, "OGG Files (*.ogg);;All FIles (*)")
        if ok:
            for fn in fns:
                if fn.endswith('.ogg'):
                    nid = os.path.split(fn)[-1][:-4]
                    nid = utilities.get_next_name(nid, [d.nid for d in RESOURCES.music])
                    new_music = Song(nid, fn)
                    RESOURCES.music.append(new_music)
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Music must be in OGG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def delete(self, idx):
        # Check to see what is using me?
        res = self._data[idx]
        nid = res.nid
        affected_levels = [level for level in DB.levels if nid in level.music.values()]
        if affected_levels:
            affected = Data(affected_levels)
            from app.editor.level_menu import LevelModel
            model = LevelModel
            msg = "Deleting Music <b>%s</b> would affect these levels."
            ok = DeletionDialog.inform(affected, model, msg, self.window)
            if ok:
                pass
            else:
                return
        super().delete(idx)

    def nid_change_watchers(self, music, old_nid, new_nid):
        # What uses music
        # Levels
        for level in DB.levels:
            for key, value in level.music:
                if value == old_nid:
                    level.music[key] = new_nid

class MusicProperties(QWidget):
    default_text = "Stopped"

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window
        self.main_editor = self.resource_editor.window

        self.current = current

        self.playing: bool = False
        self.paused: bool = False

        self.status_label = QLabel(self.default_text)

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

        hbox_layout.addWidget(self.status_label)
        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.stop_button)

        self.nid_label = QLabel("Nothing is here yet")
        self.nid_label.setStyleSheet("font-weight: bold")
        layout.addWidget(self.nid_label)
        layout.addLayout(hbox_layout)

        time_layout = QHBoxLayout()
        time_layout.setAlignment(Qt.AlignTop)

        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.time_label)

        layout.addLayout(time_layout)

        battle_section = QVBoxLayout()

        self.battle_label = QLabel("Battle Variant -- None")
        self.battle_label.setStyleSheet("font-weight: bold")
        battle_section.addWidget(self.battle_label)

        battle_load_section = QHBoxLayout()
        self.battle_check = QCheckBox("Battle Mode")
        self.battle_check.setEnabled(False)
        self.battle_check.toggled.connect(self.on_battle_toggled)
        battle_load_section.addWidget(self.battle_check)
        battle_button = QPushButton("Load Battle Variant")
        battle_button.clicked.connect(self.load_battle_variant)
        battle_load_section.addWidget(battle_button)

        battle_section.addLayout(battle_load_section)

        layout.addLayout(battle_section)

        # Double-click vagaries
        view = self.window.left_frame.view
        view.doubleClicked.connect(self.on_double_click)
        view.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Remove edit on double click

        TIMER.tick_elapsed.connect(self.tick)

    def tick(self):
        if self.paused:
            pass  # No changes
        elif self.playing:
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

    def on_double_click(self, index):
        new_music = RESOURCES.music[index.row()]
        self.set_current(new_music)
        self.play_music(self.current)
        self.stop_button.setEnabled(True)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def set_current(self, current):
        self.stop_clicked()
        self.current = current
        self.nid_label.setText(self.current.nid)

        # Handle battle variant
        self.battle_check.setChecked(False)
        if self.current.battle_full_path:
            print(self.current.battle_full_path, flush=True)
            name = os.path.split(self.current.battle_full_path[:-4])[-1]
            self.battle_label.setText("Battle Variant -- %s" % name)
            self.battle_check.setEnabled(True)
        else:
            self.battle_label.setText("Battle Variant -- None")
            self.battle_check.setEnabled(False)

    def slider_pressed(self):
        self.resource_editor.music_player.pause()
        self.paused = True

    def slider_released(self):
        cur = int(self.time_slider.value())
        self.resource_editor.music_player.set_position(cur)
        self.resource_editor.music_player.unpause()
        self.paused = False

    def play_clicked(self):
        if self.playing:
            self.pause_music()
            self.stop_button.setEnabled(False)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.current:
            self.play_music(self.current)
            self.stop_button.setEnabled(True)
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def stop_clicked(self):
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.stop_button.setEnabled(False)
        self.stop_music()

    def play_music(self, music):
        fn = music.full_path

        new_song = self.resource_editor.music_player.play(fn)

        if new_song:
            self.time_slider.setRange(0, self.resource_editor.music_player.duration)
            print("Time Slider Maximum: %d" % self.time_slider.maximum())
            self.time_slider.setValue(0)
        
        self.playing = True
        self.paused = False
        self.status_label.setText("Playing")

    def pause_music(self):
        self.playing = False
        self.paused = True
        self.resource_editor.music_player.pause()
        self.status_label.setText("Paused")
        
    def stop_music(self):
        self.playing = False
        self.paused = False
        self.status_label.setText(self.default_text)
        self.resource_editor.music_player.stop()

    def on_battle_toggled(self, checked):
        print(self.current)
        print(self.current.battle_full_path)
        if checked and self.current and self.current.battle_full_path:
            # Stop current music
            self.resource_editor.music_player.stop()
            fn = self.current.battle_full_path
            self.resource_editor.music_player.play(fn)
            # And play battle variant from where we left off
            cur = int(self.time_slider.value())
            self.resource_editor.music_player.set_position(cur)
        elif not checked and self.current:
            # Stop current music
            self.resource_editor.music_player.stop()
            fn = self.current.full_path
            self.resource_editor.music_player.play(fn)
            # And play regular variant from where we left off
            cur = int(self.time_slider.value())
            self.resource_editor.music_player.set_position(cur)

    def load_battle_variant(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fn, ok = QFileDialog.getOpenFileName(self.window, "Select Music File", starting_path, "OGG Files (*.ogg);;All FIles (*)")
        if ok:
            if fn.endswith('.ogg'):
                self.current.set_battle_full_path(fn)
                name = os.path.split(fn[:-4])[-1]
                self.battle_label.setText("Battle Variant -- %s" % name)
                self.battle_check.setEnabled(True)
                print(self.current.battle_full_path)
            else:
                QMessageBox.critical(self.window, "File Type Error!", "Music must be in OGG format!")
            parent_dir = os.path.split(fn)[0]
            settings.setValue("last_open_path", parent_dir)
