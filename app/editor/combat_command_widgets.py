import functools

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QToolButton, \
    QSpinBox, QLineEdit, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor

from app.editor.frame_selector import FrameSelector
from app.extensions.color_icon import ColorIcon

class CombatCommand(QWidget):
    def __init__(self, data, parent):
        super().__init__(parent)
        self._data = data
        self.window = parent

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

        name_label = QLabel(self._data.name)
        hbox.addWidget(name_label)

        self.create_editor(hbox)

        x_button = QToolButton(self)
        x_button.setIcon(QIcon("icons/x.png"))
        x_button.setStyleSheet("QToolButton { border: 0px solid #575757; background-color: palette(base); }")
        x_button.clicked.connect(functools.partial(self.window.remove_command, self._data))
        hbox.addWidget(x_button, Qt.AlignRight)

    def create_editor(self, hbox):
        raise NotImplementedError

    def on_value_changed(self, val):
        self._data.value = val

    @property
    def data(self):
        return self._data

class BasicCommand(CombatCommand):
    def create_editor(self, hbox):
        pass

    def on_value_changed(self, val):
        pass

class IntCommand(CombatCommand):
    def create_editor(self, hbox):
        label = QLabel("#")
        hbox.addWidget(label)

        self.editor = QSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setRange(0, 1024)
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

class SoundCommand(CombatCommand):
    def create_editor(self, hbox):
        self.editor = QLineEdit(self)
        self.editor.setPlaceholderText('Sound to play')
        self.editor.setMaximumWidth(100)
        self.editor.setReadOnly(True)
        self.editor.textChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

        self.button = QPushButton('...')
        self.button.setMaximumWidth(40)
        self.button.clicked.connect(self.select_sound)
        hbox.addWidget(self.button)

    def select_sound(self):
        from app.editor.resource_editor import ResourceEditor
        res, ok = ResourceEditor.get(self, "SFX")
        if ok:
            self.editor.setText(res.nid)

class SimpleFrameCommand(CombatCommand):
    def create_editor(self, hbox):
        self.editor = QLineEdit(self)
        self.editor.setPlaceholderText('Image to be displayed')
        self.editor.setMaximumWidth(100)
        self.editor.setReadOnly(True)
        self.editor.textChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

        self.button = QPushButton('...')
        self.button.setMaximumWidth(40)
        self.button.clicked.connect(self.select_frame)
        hbox.addWidget(self.button)

    def select_frame(self):
        res, ok = FrameSelector.get(self.window.current_frames, self.window)
        if ok:
            self.editor.setText(res)

class FrameCommand(CombatCommand):
    def create_editor(self, hbox):
        label = QLabel("#")
        hbox.addWidget(label)

        self.num_frames = QSpinBox(self)
        self.num_frames.setMaximumWidth(40)
        self.num_frames.setRange(0, 1024)
        self.num_frames.setValue(self._data.value[0])
        self.num_frames.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.num_frames)

        self.frame = QLineEdit(self)
        self.frame.setMaximumWidth(100)
        self.frame.setPlaceholderText('Frame')
        self.frame.setReadOnly(True)
        self.frame.textChanged.connect(self.on_value_changed)
        hbox.addWidget(self.frame)

        self.button = QPushButton('...')
        self.button.setMaximumWidth(40)
        self.button.clicked.connect(self.select_frame)
        hbox.addWidget(self.button)

    def on_value_changed(self, val):
        num_frames = int(self.num_frames.value())
        frame = self.frame.text()
        self._data.value = (num_frames, frame)

    def select_frame(self):
        res, ok = FrameSelector.get(self.window.current_frames, self.window)
        if ok:
            self.frame.setText(res)

class ColorTimeCommand(CombatCommand):
    def create_editor(self, hbox):
        label = QLabel("# Frames: ")
        hbox.addWidget(label)

        self.num_frames = QSpinBox(self)
        self.num_frames.setMaximumWidth(40)
        self.num_frames.setRange(0, 1024)
        self.num_frames.setValue(self._data.value[0])
        self.num_frames.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.num_frames)

        self.color = ColorIcon(QColor(248, 248, 248).name(), self)
        self.color.colorChanged.connect(self.on_value_changed)
        hbox.addWidget(self.color)

    def on_value_changed(self, val):
        num_frames = int(self.num_frame.value())
        color = self.color.color().getRgb()
        self._data.value = (num_frames, color)

def get_command_widget(command, parent):
    if command.attr is None:
        c = BasicCommand(command, parent)
    elif command.attr is int:
        c = IntCommand(command, parent)
    elif command.attr == 'sound':
        c = SoundCommand(command, parent)
    elif command.attr == 'frame':
        c = SimpleFrameCommand(command, parent)
    elif command.nid == 'frame':
        c = FrameCommand(command, parent)
    elif command.nid == 'foreground_blend':
        c = ColorTimeCommand(command, parent)
    else:  # TODO
        c = BasicCommand(command, parent)
    return c
