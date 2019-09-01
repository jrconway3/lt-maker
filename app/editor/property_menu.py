import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QFileDialog, QLineEdit, \
    QWidget, QCheckBox, QPushButton, QMessageBox
from PyQt5.QtCore import QDir

from app.data.database import DB

from app.editor.custom_gui import LineSearch
import app.utilities as utilities

class MusicDialog(QDialog):
    def __init__(self, parent, level):
        super().__init__(parent)
        self.setWindowTitle('Level Music')
        self.level = level

        form = QFormLayout(self)
        form.setVerticalSpacing(0)

        self.music_boxes = {}
        for key in self.level.music.keys():
            box = LineSearch(self)
            box.set_func(lambda: self.find_music(box.line_edit, key))
            form.addRow(key.replace('_', ' ').capitalize(), box)
            self.music_boxes[key] = box

        self.load(self.level.music)

    def find_music(self, line_edit, music_path):
        starting_path = QDir.currentPath()
        music_file, _ = QFileDialog.getOpenFileName(self, "Select Music File", starting_path,
                                                    "OGG Files (*.ogg);;All Files (*)")
        if music_file:
            head, tail = os.path.split(music_file)
            print(head)
            # if os.path.normpath(head) != os.path.normpath(starting_path):
            #     print('Copying ' + music_file + ' to ' + starting_path)
            #     shutil.copy(music_file, starting_path)
            line_edit.setText(tail.split('.')[0])
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
        self.level = self.main_editor.current_level

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

    def nid_changed(self, text):
        self.level.nid = text
        self.main_editor.update_view()

    def nid_done_editing(self):
        other_nids = [level.nid for level in DB.level_list if level is not self.level]
        if self.level.nid in other_nids:
            QMessageBox.warning(self, 'Warning', 'Level ID %s already in use' % self.level.nid)
            self.level.nid = utilities.get_next_int(self.level.nid, other_nids)
        self.main_editor.update_view()

    def name_changed(self, text):
        self.level.name = text
        self.main_editor.update_view()

    def market_changed(self, state):
        self.level.market_flag = state

    def edit_music(self):
        dlg = MusicDialog(self)
        dlg.exec_()

    def set_objective(self, key):
        if key == 'simple':
            self.level.objective[key] = self.quick_display.text()
        elif key == 'win':
            self.level.objective[key] = self.win_condition.text()
        elif key == 'loss':
            self.level.objective[key] = self.loss_condition.text()
