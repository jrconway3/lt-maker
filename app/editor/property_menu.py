from functools import partial

from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, \
    QWidget, QCheckBox, QPushButton, QMessageBox, QLabel
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.extensions.custom_gui import SimpleDialog, PropertyBox, PropertyCheckBox
from app.editor.resource_editor import ResourceEditor
import app.utilities as utilities

class MusicDialog(SimpleDialog):
    def __init__(self, parent, current):
        super().__init__(parent)
        self.window = parent
        self.main_editor = self.window.main_editor
        self.setWindowTitle("Level Music")
        self.current = current

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.boxes = {}
        for idx, key in enumerate(self.current.music.keys()):
            title = key.replace('_', ' ').title()
            box = PropertyBox(title, QLineEdit, self)
            box.edit.setReadOnly(True)
            box.add_button(QPushButton('...'))
            box.button.setMaximumWidth(40)
            box.button.clicked.connect(partial(self.access_music_resources, key))

            layout.addWidget(box)
            self.boxes[key] = box

        self.set_current(self.current)

    def set_current(self, current):
        self.current = current
        for key, value in self.current.music.items():
            if value:
                self.boxes[key].edit.setText(value)

    def access_music_resources(self, key):
        res, ok = ResourceEditor.get(self, "Music")
        if ok:
            nid = res.nid
            self.current.music[key] = nid
            self.boxes[key].edit.setText(nid)

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

    def on_visibility_changed(self, state):
        if state:
            if self.main_editor.current_level is not self.current:
                self.set_current(self.main_editor.current_level)

    def tick(self):
        pass

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

    def set_objective(self, key):
        if key == 'simple':
            self.current.objective[key] = self.quick_display.edit.text()
        elif key == 'win':
            self.current.objective[key] = self.win_condition.edit.text()
        elif key == 'loss':
            self.current.objective[key] = self.loss_condition.edit.text()
