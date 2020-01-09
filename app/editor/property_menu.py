import os
from functools import partial

from PyQt5.QtWidgets import QVBoxLayout, QFileDialog, QLineEdit, \
    QWidget, QCheckBox, QPushButton, QMessageBox, QGridLayout, QLabel, \
    QToolButton, QStyle
from PyQt5.QtMultimedia import QMediaPlaylist
from PyQt5.QtCore import Qt, QDir, QUrl

from app.data.database import DB

from app.editor.custom_gui import SimpleDialog, LineSearch, PropertyBox, PropertyCheckBox
import app.utilities as utilities

class MusicDialog(SimpleDialog):
    def __init__(self, parent, level):
        super().__init__(parent)
        self.properties = parent
        self.main_editor = parent.main_editor
        self.setWindowTitle('Level Music')
        self.level = level

        form = QGridLayout(self)
        form.setVerticalSpacing(0)

        self.music_boxes = {}
        self.play_buttons = {}
        self.stop_buttons = {}
        self.play_state = {}
        for idx, key in enumerate(self.level.music.keys()):
            box = LineSearch(self)
            box.search_button.clicked.connect(partial(self.find_music, key))
            form.addWidget(QLabel(key.replace('_', ' ').capitalize()), idx, 0)
            form.addWidget(box, idx, 1)

            play_button = QToolButton(self)
            self.play_buttons[key] = play_button
            if key == self.properties.currently_playing:
                self.play_state[key] = True
                play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            else:
                self.play_state[key] = False
                play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            play_button.clicked.connect(partial(self.play_clicked, key))
            form.addWidget(play_button, idx, 2)

            stop_button = QToolButton(self)
            self.stop_buttons[key] = stop_button
            stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            if key == self.properties.currently_playing:
                stop_button.setEnabled(True)
            else:
                stop_button.setEnabled(False)
            stop_button.clicked.connect(partial(self.stop_clicked, key))
            form.addWidget(stop_button, idx, 3)

            self.music_boxes[key] = box

        self.set_current(self.level.music)

    def find_music(self, music_key):
        print(music_key)
        starting_path = QDir.currentPath()
        music_file, _ = QFileDialog.getOpenFileName(self, "Select Music File", starting_path,
                                                    "OGG Files (*.ogg);;All Files (*)")
        if music_file:
            head, tail = os.path.split(music_file)
            # if os.path.normpath(head) != os.path.normpath(starting_path):
            #     print('Copying ' + music_file + ' to ' + starting_path)
            #     shutil.copy(music_file, starting_path)
            self.music_boxes[music_key].line_edit.setText(tail.split('.')[0])
            self.level.music[music_key] = music_file

    def set_current(self, music_dict):
        for key, value in music_dict.items():
            if value:
                head, tail = os.path.split(value)
                self.music_boxes[key].line_edit.setText(tail.split('.')[0])

    def pause_music(self, music_key):
        self.play_button[music_key].setIcon(QStyle.SP_MediaPlay)
        self.play_state[music_key] = False
        self.main_editor.music_player.pause()
        self.properties.set_currently_playing(None)

    def play_clicked(self, music_key):
        # If currently playing
        if self.play_state[music_key]:
            self.pause_music(music_key)
        else:
            # If something else is already playing
            if self.properties.currently_playing:
                self.play_button[self.properties.currently_playing].setIcon(QStyle.SP_MediaPlay)
                self.play_state[self.properties.currently_playing] = False
                self.stop_state[self.properties.currently_playing].setEnabled(False)
            if self.level.music[music_key]:
                self.play_button[music_key].setIcon(QStyle.SP_MediaPause)
                self.play_state[music_key] = True
                self.properties.set_currently_playing(music_key)
                self.stop_state[music_key].setEnabled(True)
                # Actually play music
                playlist = QMediaPlaylist()
                playlist.addMedia(QUrl.fromLocalFile(self.level.music[music_key]))
                playlist.setPlaybackMode(QMediaPlaylist.Loop)
                self.main_editor.music_player.setPlaylist(playlist)
                self.main_editor.music_player.play()

    def stop_clicked(self, music_key):
        self.play_button[music_key].setIcon(QStyle.SP_MediaPlay)
        self.play_state[music_key] = False
        self.stop_button[music_key].setEnabled(False)
        self.main_editor.music_player.stop()
        self.properties.set_currently_playing(None)

class PropertiesMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_editor = parent
        self.current = None

        self.setStyleSheet("font: 10pt;")

        form = QVBoxLayout(self)
        form.setAlignment(Qt.AlignTop)

        self.nid_box = PropertyBox("Level ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        form.addWidget(self.nid_box)

        self.title_box = PropertyBox("Level Title", QLineEdit, self)
        self.title_box.edit.textChanged.connect(self.title_changed)
        form.addWidget(self.title_box)

        self.market_box = PropertyCheckBox("Market Available?", QCheckBox, self)
        self.market_box.edit.stateChanged.connect(self.market_changed)
        form.addWidget(self.market_box)

        self.music_button = QPushButton("Edit Level's Music...", self)
        self.music_button.clicked.connect(self.edit_music)
        form.addWidget(self.music_button)

        self.currently_playing = None
        self.currently_playing_label = QLabel("")
        form.addWidget(self.currently_playing_label)

        self.quick_display = PropertyBox("Objective Display", QLineEdit, self)
        self.quick_display.edit.editingFinished.connect(lambda: self.set_objective('simple'))
        form.addWidget(self.quick_display)

        self.win_condition = PropertyBox("Win Condition", QLineEdit, self)
        self.win_condition.edit.editingFinished.connect(lambda: self.set_objective('win'))
        form.addWidget(self.win_condition)

        self.loss_condition = PropertyBox("Loss Condition", QLineEdit, self)
        self.loss_condition.edit.editingFinished.connect(lambda: self.set_objective('loss'))
        form.addWidget(self.loss_condition)

        if self.main_editor.current_level:
            self.set_current(self.main_editor.current_level)

    def set_current(self, current):
        self.current = current

        self.title_box.edit.setText(current.title)
        self.nid_box.edit.setText(current.nid)
        self.market_box.edit.setChecked(current.market_flag)
        self.quick_display.edit.setText(current.objective['simple'])
        self.win_condition.edit.setText(current.objective['win'])
        self.loss_condition.edit.setText(current.objective['loss'])

        self.currently_playing = None
        self.main_editor.music_player.stop()

    def on_visibility_changed(self, state):
        if state:
            if self.main_editor.current_level is not self.current:
                self.set_current(self.main_editor.current_level)

    def nid_changed(self, text):
        self.current.nid = text
        self.main_editor.update_view()

    def nid_done_editing(self):
        other_nids = [level.nid for level in DB.levels if level is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self, 'Warning', 'Level ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_int(self.current.nid, other_nids)
        DB.levels.update_nid(self.current, self.current.nid)
        self.main_editor.update_view()

    def title_changed(self, text):
        self.current.title = text
        self.main_editor.update_view()

    def market_changed(self, state):
        self.current.market_flag = bool(state)

    def edit_music(self):
        dlg = MusicDialog(self, self.current)
        dlg.exec_()

    def set_currently_playing(self, music_key):
        if music_key:
            music_path = self.current.music[music_key]
            head, tail = os.path.split(music_path)
            self.currently_playing_label.setText("Currently Playing %s" % tail)
        else:
            self.currently_playing_label.setText("")

    def set_objective(self, key):
        if key == 'simple':
            self.current.objective[key] = self.quick_display.edit.text()
        elif key == 'win':
            self.current.objective[key] = self.win_condition.edit.text()
        elif key == 'loss':
            self.current.objective[key] = self.loss_condition.edit.text()
