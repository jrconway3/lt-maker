import os
from functools import partial

from PyQt5.QtWidgets import QFormLayout, QFileDialog, QLineEdit, \
    QWidget, QCheckBox, QPushButton, QMessageBox, QGridLayout, QLabel, \
    QToolButton, QStyle
from PyQt5.QtMultimedia import QMediaPlaylist
from PyQt5.QtCore import QDir, QUrl

from app.data.database import DB

from app.editor.custom_gui import SimpleDialog, LineSearch
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

        self.load(self.level.music)

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

    def load(self, music_dict):
        for key, value in music_dict.items():
            if value:
                head, tail = os.path.split(value)
                self.music_boxes[key].line_edit.setText(tail.split('.')[0])

    def play_clicked(self, music_key):
        # If currently playing
        if self.play_state[music_key]:
            self.play_button[music_key].setIcon(QStyle.SP_MediaPlay)
            self.play_state[music_key] = False
            self.main_editor.music_player.pause()
            self.properties.set_currently_playing(None)
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
        self.current_level = self.main_editor.current_level

        form = QFormLayout(self)

        self.level_name = QLineEdit(self)
        self.level_name.textChanged.connect(self.name_changed)
        form.addRow('Level Name:', self.level_name)

        self.level_nid = QLineEdit(self)
        self.level_nid.textChanged.connect(self.nid_changed)
        self.level_nid.editingFinished.connect(self.nid_done_editing)
        form.addRow('Level ID:', self.level_nid)

        self.market_check = QCheckBox(self)
        self.market_check.stateChanged.connect(self.market_changed)
        form.addRow('Market Available?', self.market_check)

        self.music_button = QPushButton('Edit Music...', self)
        self.music_button.clicked.connect(self.edit_music)
        form.addRow('Level Music:', self.music_button)

        self.currently_playing = None
        self.currently_playing_label = QLabel("")
        form.addRow(self.currently_playing_label)

        self.quick_display = QLineEdit(self)
        self.quick_display.editingFinished.connect(lambda: self.set_objective('simple'))
        form.addRow('Objective Display:', self.quick_display)

        self.win_condition = QLineEdit(self)
        self.win_condition.editingFinished.connect(lambda: self.set_objective('win'))
        form.addRow('Win Condition:', self.win_condition)

        self.loss_condition = QLineEdit(self)
        self.loss_condition.editingFinished.connect(lambda: self.set_objective('loss'))
        form.addRow('Loss Condition:', self.loss_condition)

    def on_visibility_changed(self, state):
        if state:
            self.current_level = self.main_editor.current_level

    def nid_changed(self, text):
        self.current_level.nid = text
        self.main_editor.update_view()

    def nid_done_editing(self):
        current = self.current_level
        other_nids = [level.nid for level in DB.level_list if level is not current]
        if current.nid in other_nids:
            QMessageBox.warning(self, 'Warning', 'Level ID %s already in use' % current.nid)
            current.nid = utilities.get_next_int(current.nid, other_nids)
        self.main_editor.update_view()

    def name_changed(self, text):
        self.current_level.name = text
        self.main_editor.update_view()

    def market_changed(self, state):
        self.current_level.market_flag = state

    def edit_music(self):
        dlg = MusicDialog(self, self.current_level)
        dlg.exec_()

    def set_currently_playing(self, music_key):
        if music_key:
            music_path = self.current_level.music[music_key]
            head, tail = os.path.split(music_path)
            self.currently_playing_label.setText("Currently Playing %s" % tail)
        else:
            self.currently_playing_label.setText("")

    def set_objective(self, key):
        if key == 'simple':
            self.current_level.objective[key] = self.quick_display.text()
        elif key == 'win':
            self.current_level.objective[key] = self.win_condition.text()
        elif key == 'loss':
            self.current_level.objective[key] = self.loss_condition.text()
