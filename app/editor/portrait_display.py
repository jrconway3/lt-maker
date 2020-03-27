from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, QMessageBox, \
    QSpinBox, QLabel, QVBoxLayout, QGridLayout, QPushButton, QSizePolicy, QFrame, \
    QSplitter
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QSettings
from PyQt5.QtGui import QPixmap, QIcon, QPainter

import os
import time, random

from app.data.resources import RESOURCES
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ResourceListView
from app.editor.timer import TIMER
from app.editor.base_database_gui import DatabaseTab, ResourceCollectionModel
from app.editor.icon_display import IconView

from app import utilities

class PortraitDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.portraits
        title = "Unit Portrait"
        right_frame = PortraitProperties
        collection_model = PortraitModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceListView)
        return dialog

class PortraitModel(ResourceCollectionModel):
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

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Choose %s", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]
                    pix = QPixmap(fn)
                    nid = utilities.get_next_name(nid, [d.nid for d in RESOURCES.portraits])
                    if pix.width() == 128 and pix.height() == 112:
                        RESOURCES.create_new_portrait(nid, fn, pix)
                    else:
                        QMessageBox.critical(self.window, "Error", "Image is not correct size (128x112 px)")
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Portrait must be PNG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def nid_change_watchers(self, portrait, old_nid, new_nid):
        # What uses portraits
        # Units (Later Dialogues)
        for unit in DB.units:
            if unit.portrait_nid == old_nid:
                unit.portrait_nid = new_nid

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

    halfblink = (96, 48, 32, 16)
    fullblink = (96, 64, 32, 16)

    openmouth = (0, 96, 32, 16)
    halfmouth = (32, 96, 32, 16)
    closemouth = (64, 96, 32, 16)

    opensmile = (0, 80, 32, 16)
    halfsmile = (32, 80, 32, 16)
    closesmile = (64, 80, 32, 16)

    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        self.current = current

        self.smile_on = False
        self.talk_on = False
        # For talking
        self.talk_state = 0
        self.last_talk_update = 0
        self.next_talk_update = 0
        # For blinking
        self.blink_update = 0

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
        self.blink_button.clicked.connect(self.blink_button_clicked)
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

        TIMER.tick_elapsed.connect(self.tick)

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

    def update_talk(self):
        current_time = time.time()*1000
        # update mouth
        if self.talk_on and current_time - self.last_talk_update > self.next_talk_update:
            self.last_talk_update = current_time
            chance = random.randint(1, 10)
            if self.talk_state == 0:
                # 10% chance to skip to state 2    
                if chance == 1:
                    self.talk_state = 2
                    self.next_talk_update = random.randint(70, 160)
                else:
                    self.talk_state = 1
                    self.next_talk_update = random.randint(30, 50)
            elif self.talk_state == 1:
                # 10% chance to go back to state 0
                if chance == 1:
                    self.talk_state = 0
                    self.next_talk_update = random.randint(50, 100)
                else:
                    self.talk_state = 2
                    self.next_talk_update = random.randint(70, 160)
            elif self.talk_state == 2:
                # 10% chance to skip back to state 0
                # 10% chance to go back to state 1
                chance = random.randint(1, 10)
                if chance == 1:
                    self.talk_state = 0
                    self.next_talk_update = random.randint(50, 100)
                elif chance == 2:
                    self.talk_state = 1
                    self.next_talk_update = random.randint(30, 50)
                else:
                    self.talk_state = 3
                    self.next_talk_update = random.randint(30, 50)
            elif self.talk_state == 3:
                self.talk_state = 0
                self.next_talk_update = random.randint(50, 100)
        if not self.talk_on:
            self.talk_state = 0

    def draw_portrait(self):
        self.update_talk()
        portrait = self.current.pixmap.copy(0, 0, 96, 80).toImage()
        # For smile image
        if self.smile_on:
            if self.talk_state == 0:
                mouth_image = self.current.pixmap.copy(*self.closesmile)
            elif self.talk_state == 1 or self.talk_state == 3:
                mouth_image = self.current.pixmap.copy(*self.halfsmile)
            elif self.talk_state == 2:
                mouth_image = self.current.pixmap.copy(*self.opensmile)
        else:
            if self.talk_state == 0:
                mouth_image = self.current.pixmap.copy(*self.closemouth)
            elif self.talk_state == 1 or self.talk_state == 3:
                mouth_image = self.current.pixmap.copy(*self.halfmouth)
            elif self.talk_state == 2:
                mouth_image = self.current.pixmap.copy(*self.openmouth)
        mouth_image = mouth_image.toImage()
        # For blink image
        time_passed = time.time()*1000 - self.blink_update
        if time_passed < 60:
            blink_image = self.current.pixmap.copy(*self.halfblink)
        elif time_passed < 120:
            blink_image = self.current.pixmap.copy(*self.fullblink)
        elif time_passed < 180:
            blink_image = self.current.pixmap.copy(*self.halfblink)
        else:
            blink_image = None
        # Draw image
        painter = QPainter()
        painter.begin(portrait)
        if blink_image:
            blink_image = blink_image.toImage()
            painter.drawImage(self.current.blinking_offset[0], self.current.blinking_offset[1], blink_image)
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

    def blink_button_clicked(self):
        self.blink_update = time.time()*1000
