import os
from functools import partial

from PyQt5.QtWidgets import QFormLayout, QFileDialog, QLineEdit, \
    QWidget, QCheckBox, QPushButton, QMessageBox, QGridLayout, QLabel
from PyQt5.QtCore import QDir

from app.data.database import DB

from app.editor.custom_gui import EditDialog, LineSearch
import app.utilities as utilities

class MusicDialog(EditDialog):
    def __init__(self, parent, level):
        super().__init__(parent)
        self.setWindowTitle('Level Music')
        self.level = level

        form = QGridLayout(self)
        form.setVerticalSpacing(0)

        self.music_boxes = {}
        for idx, key in enumerate(self.level.music.keys()):
            box = LineSearch(self)
            box.search_button.clicked.connect(partial(self.find_music, key))
            form.addWidget(QLabel(key.replace('_', ' ').capitalize()), idx, 0)
            form.addWidget(box, idx, 1)
            self.music_boxes[key] = box

        self.load(self.level.music)

    def find_music(self, music_path):
        print(music_path)
        starting_path = QDir.currentPath()
        music_file, _ = QFileDialog.getOpenFileName(self, "Select Music File", starting_path,
                                                    "OGG Files (*.ogg);;All Files (*)")
        if music_file:
            head, tail = os.path.split(music_file)
            # if os.path.normpath(head) != os.path.normpath(starting_path):
            #     print('Copying ' + music_file + ' to ' + starting_path)
            #     shutil.copy(music_file, starting_path)
            self.music_boxes[music_path].line_edit.setText(tail.split('.')[0])
            self.level.music[music_path] = music_file

    def load(self, music_dict):
        for key, value in music_dict.items():
            if value:
                head, tail = os.path.split(value)
                self.music_boxes[key].line_edit.setText(tail.split('.')[0])

class PropertiesMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_editor = parent

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

        self.quick_display = QLineEdit(self)
        self.quick_display.editingFinished.connect(lambda: self.set_objective('simple'))
        form.addRow('Objective Display:', self.quick_display)

        self.win_condition = QLineEdit(self)
        self.win_condition.editingFinished.connect(lambda: self.set_objective('win'))
        form.addRow('Win Condition:', self.win_condition)

        self.loss_condition = QLineEdit(self)
        self.loss_condition.editingFinished.connect(lambda: self.set_objective('loss'))
        form.addRow('Loss Condition:', self.loss_condition)

    def get_current_level(self):
        return self.main_editor.current_level

    def nid_changed(self, text):
        self.get_current_level().nid = text
        self.main_editor.update_view()

    def nid_done_editing(self):
        current = self.get_current_level()
        other_nids = [level.nid for level in DB.level_list if level is not current]
        if current.nid in other_nids:
            QMessageBox.warning(self, 'Warning', 'Level ID %s already in use' % current.nid)
            current.nid = utilities.get_next_int(current.nid, other_nids)
        self.main_editor.update_view()

    def name_changed(self, text):
        self.get_current_level().name = text
        self.main_editor.update_view()

    def market_changed(self, state):
        self.get_current_level().market_flag = state

    def edit_music(self):
        dlg = MusicDialog(self, self.get_current_level())
        dlg.exec_()

    def set_objective(self, key):
        if key == 'simple':
            self.get_current_level().objective[key] = self.quick_display.text()
        elif key == 'win':
            self.get_current_level().objective[key] = self.win_condition.text()
        elif key == 'loss':
            self.get_current_level().objective[key] = self.loss_condition.text()
