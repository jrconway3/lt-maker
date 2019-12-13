from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, \
    QSpinBox, QLabel, QVBoxLayout, QGridLayout, QPushButton, QSizePolicy, QFrame, \
    QSplitter
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QPainter

import os

from app.data.resources import RESOURCES

from app.editor.custom_gui import PropertyBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.icon_database import IconView

class PortraitDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.portraits
        title = "Unit Portrait"
        right_frame = PortraitProperties
        collection_model = PortraitModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...")
        return dialog

    def create_new(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self, "Choose %s", starting_path)
        if ok:
            if fn.endswith('.png'):
                local_name = os.path.split(fn)[-1]
                pix = QPixmap(fn)
                if pix.width() == 128 and pix.height() == 112:
                    RESOURCES.create_new_portrait(local_name, pix)
                    self.after_new()
                else:
                    QMessageBox.critical(self, "Error", "Image is not correct size (128x112 px)")

class PortraitModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            portrait = self._data[index.row()]
            text = portrait.nid
            return text
        elif role == Qt.DecorationRole:
            portrait = self._data[index.row()]
            pixmap = portrait.pixmap
            chibi = pixmap.copy(96, 16, 32, 32)
            return QIcon(chibi)
        return None

class SpinBoxXY(QWidget):
    coordsChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        hbox = QHBoxLayout()
        self.setLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(1)

        self._x = 0
        self._y = 0

        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        self.x_spinbox.setMinimumWidth(40)
        self.y_spinbox.setMinimumWidth(40)
        x_label = QLabel("X:")
        y_label = QLabel("Y:")
        hbox.addWidget(x_label)
        hbox.addWidget(self.x_spinbox)
        hbox.addWidget(y_label)
        hbox.addWidget(self.y_spinbox)
        self.x_spinbox.setRange(0, 128 - 16)
        self.y_spinbox.setRange(0, 112 - 16)
        self.x_spinbox.setSingleStep(8)
        self.y_spinbox.setSingleStep(8)
        self.x_spinbox.valueChanged.connect(self.change_x)
        self.y_spinbox.valueChanged.connect(self.change_y)
        self.x_spinbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.y_spinbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        x_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        y_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedWidth(140)
        # hbox.setAlignment(Qt.AlignLeft)

    def set_current(self, x, y):
        self.change_x(x)
        self.change_y(y)

    def change_x(self, value):
        self._x = value
        self.x_spinbox.setValue(self._x)
        self.coordsChanged.emit(self._x, self._y)

    def change_y(self, value):
        self._y = value
        self.y_spinbox.setValue(self._y)
        self.coordsChanged.emit(self._x, self._y)

class PortraitProperties(QWidget):
    width, height = 128, 112

    openmouth = (0, 96, 32, 16)
    halfmouth = (32, 96, 32, 16)
    closemouth = (64, 96, 32, 16)

    opensmile = (0, 80, 32, 16)
    halfsmile = (32, 80, 32, 16)
    closesmile = (64, 80, 32, 16)

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        self.current = current

        self.smile_on = False
        self.talk_on = False

        # === Timing ===
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.tick)
        fps = 30
        timer_speed = int(1000/float(fps))
        self.main_timer.setInterval(timer_speed)
        self.main_timer.start()

        left_section = QGridLayout()

        self.portrait_view = IconView(self)
        left_section.addWidget(self.portrait_view, 0, 0, 1, 3)

        self.smile_button = QPushButton(self)
        self.smile_button.setText("Smile")
        self.smile_button.setCheckable(True)
        self.smile_button.clicked.connect(self.smile_button_clicked)
        self.talk_button = QPushButton(self)
        self.talk_button.setText("Talk")
        self.talk_button.setCheckable(True)
        self.talk_button.clicked.connect(self.talk_button_clicked)
        self.blink_button = QPushButton(self)
        self.blink_button.setText("Blink")
        left_section.addWidget(self.smile_button)
        left_section.addWidget(self.talk_button)
        left_section.addWidget(self.blink_button)

        right_section = QVBoxLayout()
        self.blinking_offset = PropertyBox("Blinking Offset", SpinBoxXY, self)
        self.blinking_offset.edit.coordsChanged.connect(self.blinking_changed)
        self.smiling_offset = PropertyBox("Smiling Offset", SpinBoxXY, self)
        self.smiling_offset.edit.coordsChanged.connect(self.smiling_changed)
        right_section.addWidget(self.blinking_offset)
        right_section.addWidget(self.smiling_offset)
        right_section.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        left_frame = QFrame(self)
        left_frame.setLayout(left_section)
        right_frame = QFrame(self)
        right_frame.setLayout(right_section)

        top_splitter = QSplitter(self)
        top_splitter.setChildrenCollapsible(False)
        top_splitter.addWidget(left_frame)
        top_splitter.addWidget(right_frame)

        self.raw_view = PropertyBox("Raw Sprite", IconView, self)
        self.raw_view.edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        final_splitter = QSplitter(self)
        final_splitter.setOrientation(Qt.Vertical)
        final_splitter.setChildrenCollapsible(False)
        final_splitter.addWidget(top_splitter)
        final_splitter.addWidget(self.raw_view)

        final_section = QHBoxLayout()
        self.setLayout(final_section)
        final_section.addWidget(final_splitter)

    def set_current(self, current):
        self.current = current
        self.raw_view.edit.set_image(self.current.pixmap)
        self.raw_view.edit.show_image()

        bo = self.current.blinking_offset
        so = self.current.smiling_offset
        self.blinking_offset.edit.set_current(bo[0], bo[1])
        self.smiling_offset.edit.set_current(so[0], so[1])

        self.draw_portrait()

    def tick(self):
        self.draw_portrait()

    def draw_portrait(self):
        portrait = self.current.pixmap.copy(0, 0, 96, 80).toImage()
        if self.smile_on:
            if self.talk_on:
                mouth_image = self.current.pixmap.copy(*self.opensmile)
            else:
                mouth_image = self.current.pixmap.copy(*self.closesmile)
        else:
            if self.talk_on:
                mouth_image = self.current.pixmap.copy(*self.openmouth)
            else:
                mouth_image = self.current.pixmap.copy(*self.closemouth)
        mouth_image = mouth_image.toImage()
        # Draw image
        painter = QPainter()
        painter.begin(portrait)
        painter.drawImage(self.current.smiling_offset[0], self.current.smiling_offset[1], mouth_image)
        painter.end()
        self.portrait_view.set_image(QPixmap.fromImage(portrait))
        self.portrait_view.show_image()

    def blinking_changed(self, x, y):
        self.current.blinking_offset = [x, y]

    def smiling_changed(self, x, y):
        self.current.smiling_offset = [x, y]

    def talk_button_clicked(self, checked):
        self.talk_on = checked

    def smile_button_clicked(self, checked):
        self.smile_on = checked
