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
        x_button.clicked.connect(partial(self.window.remove_component, self))
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
        label = QLabel("# Frames: ")
        hbox.addWidget(label)

        self.editor = QSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setRange(0, 1024)
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

class SimpleFrameCommand(CombatCommand):
    def create_editor(self, hbox):
        self.editor = QLineEdit(self)
        self.editor.setEmptyText('Image to be displayed')
        self.editor.setEditable(False)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

        self.button = QPushButton('...')
        self.button.setMaximumWidth(40)
        self.button.triggered.connect(self.select_frame)
        hbox.addWidget(self.button)

    def select_frame(self):
        res, ok = FrameSelector.get()
        if ok:
            self.editor.setText(res)

class FrameCommand(CombatCommand):
    def create_editor(self, hbox):
        label = QLabel("# Frames: ")
        hbox.addWidget(label)

        self.num_frames = QSpinBox(self)
        self.num_frames.setMaximumWidth(40)
        self.num_frames.setRange(0, 1024)
        self.num_frames.setValue(self._data.value[0])
        self.num_frames.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.num_frames)

        self.frame = QLineEdit(self)
        self.frame.setEmptyText('Image to be displayed')
        self.frame.setEditable(False)
        self.frame.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.frame)

        self.button = QPushButton('...')
        self.button.setMaximumWidth(40)
        self.button.triggered.connect(self.select_frame)
        hbox.addWidget(self.button)

    def on_value_changed(self, val):
        num_frames = int(self.num_frames.value())
        frame = self.frame.text()
        self._data.value = (num_frames, frame)

    def select_frame(self):
        res, ok = FrameSelector.get()
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
        self._data.value(num_frames, color)
