from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from app.data.resources import RESOURCES

from app.editor.resource_editor import ResourceEditor

class PushableIcon16(QPushButton):
    sourceChanged = pyqtSignal(str, int, int)
    width, height = 16, 16
    database = RESOURCES.icons16

    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self._nid = None
        self.x, self.y = 0, 0

        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self.setMinimumWidth(64)
        self.setMaximumWidth(64)
        self.resize(64, 64)
        self.setStyleSheet("QPushButton {qproperty-iconSize: 64px;}")
        self.pressed.connect(self.onIconSourcePicker)

    def render(self):
        if self._nid:
            res = self.database.get(self._nid)
            if not res.pixmap:
                res.pixmap = QPixmap(res.full_path)
            if res.pixmap.width() > 0 and res.pixmap.height() > 0:
                pic = res.pixmap.copy(self.x*self.width, self.y*self.height, self.width, self.height)
                pic = pic.scaled(64, 64)
                pic = QIcon(pic)
                self.setIcon(pic)
        else:
            self.setIcon(QIcon())

    def change_icon(self, nid, icon_index):
        self._nid = nid
        self.x = icon_index[0]
        self.y = icon_index[1]
        self.sourceChanged.emit(self._nid, self.x, self.y)
        self.render()

    def onIconSourcePicker(self):
        res, ok = ResourceEditor.get(self, "Icons " + str(self.width) + 'x' + str(self.height))
        if ok:
            if res.parent_image:
                nid = res.parent_image.nid
            else:
                nid = res.nid
            self.change_icon(nid, res.icon_index)

class PushableIcon32(PushableIcon16):
    width, height = 32, 32
    database = RESOURCES.icons32

class PushableIcon80(PushableIcon16):
    width, height = 80, 72
    database = RESOURCES.icons80

class ItemIcon16(QWidget):
    width, height = 16, 16
    child_icon = PushableIcon16

    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent

        hbox = QHBoxLayout()
        self.setLayout(hbox)
        hbox.setContentsMargins(0, 0, 0, 0)

        self.icon = self.child_icon(self)
        hbox.addWidget(self.icon, Qt.AlignCenter)

        self.icon.sourceChanged.connect(self.on_icon_changed)

    def set_current(self, nid, icon_index):
        self.icon.change_icon(nid, icon_index)

    def on_icon_changed(self, nid, x, y):
        if self.window.current:
            self.window.current.icon_nid = nid
            self.window.current.icon_index = (x, y)
            self.window.window.update_list()

class ItemIcon32(ItemIcon16):
    width, height = 32, 32
    child_icon = PushableIcon32

class ItemIcon80(ItemIcon16):
    width, height = 80, 72
    child_icon = PushableIcon80

class UnitPortrait(QPushButton):
    sourceChanged = pyqtSignal(str)
    width, height = 96, 80
    database = RESOURCES.portraits

    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self._nid = None

        self.setMinimumHeight(self.height)
        self.setMaximumHeight(self.height)
        self.setMinimumWidth(self.width)
        self.setMaximumWidth(self.width)
        self.resize(self.width, self.height)
        self.setStyleSheet("QPushButton {qproperty-iconSize: %dpx %dpx;}" % (self.width, self.height))
        self.pressed.connect(self.onIconSourcePicker)

    def render(self):
        if self._nid:
            res = self.database.get(self._nid)
            if not res:
                self.setIcon(QIcon())
                return
            if not res.pixmap:
                res.pixmap = QPixmap(res.full_path)
            pixmap = res.pixmap.copy(0, 0, self.width, self.height)
            pic = QIcon(pixmap)
            self.setIcon(pic)
        else:
            self.setIcon(QIcon())

    def change_icon(self, nid):
        self._nid = nid
        self.sourceChanged.emit(self._nid)
        self.render()

    def set_current(self, nid):
        self.change_icon(nid)

    def onIconSourcePicker(self):
        res, ok = ResourceEditor.get(self, "Portraits")
        if ok:
            nid = res.nid
            self.change_icon(nid)
