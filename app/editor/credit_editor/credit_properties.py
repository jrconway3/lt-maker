from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QVBoxLayout, QTextEdit, QStackedWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics, QIcon

from app.data.resources.resources import RESOURCES

from app.extensions.custom_gui import PropertyBox, ComboBox
from app.extensions.list_widgets import AppendMultiListWidget
from app.extensions.key_value_delegate import KeyValueDelegate, KeyValueDoubleListModel

from app.editor.icons import PushableIcon16
from app.editor.icon_editor import icon_tab
from app.editor.map_sprite_editor import map_sprite_tab, map_sprite_model
from app.editor.lib.components.validated_line_edit import NidLineEdit

from app.utilities import str_utils

class CreditProperties(QWidget):
    CREDIT_TYPES = ("16x16_Icons", "32x32_Icons", "80x72_Icons", "Portraits", "Map_Icons", "Map_Sprites", "Panoramas", "List", "Text")

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        self.nid_box = PropertyBox("Unique ID", NidLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)

        self.type_box = PropertyBox(("Type"), ComboBox, self)
        for type in self.CREDIT_TYPES:
            self.type_box.edit.addItem(type.replace('_', ' '))
        self.type_box.edit.currentIndexChanged.connect(self.type_changed)

        self.category_box = PropertyBox("Category", QLineEdit, self)
        self.category_box.edit.textChanged.connect(self.category_changed)

        self.desc_box = QStackedWidget(self)
        for type in self.CREDIT_TYPES:
            if type in ("16x16_Icons", "32x32_Icons", "80x72_Icons", "Portraits", "Map_Icons"):
                desc_box = IconDesc(self, type)
            elif type == "Map_Sprites":
                desc_box = MapSpriteDesc(self)
            elif type == "Panoramas":
                desc_box = PanoramaDesc(self)
            elif type == "List":
                desc_box = ListDesc(self)
            elif type == "Text":
                desc_box = TextDesc(self)    
            self.desc_box.addWidget(desc_box)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addWidget(self.nid_box)  
        total_section.addWidget(self.type_box)   
        total_section.addWidget(self.category_box)
        total_section.addWidget(self.desc_box)

        total_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Credit ID %s already in use' % self.current.nid)
            self.current.nid = str_utils.get_next_name(self.current.nid, other_nids)
        self.window.left_frame.model.on_nid_changed(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def type_changed(self, index):
        type = self.type_box.edit.currentText().replace(' ', '_')
        self.current.type = type

        if self.current.type in ["List", "Text"]:
            self.category_box.setEnabled(True)
        else:
            self.category_box.setEnabled(False)
            self.category_box.edit.setText('Graphics')

        idx = self.CREDIT_TYPES.index(type)
        self.desc_box.setCurrentIndex(idx)
        self.desc_box.currentWidget().set_current(self.current)

    def category_changed(self, category):
        self.current.category = category
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.type_box.edit.setValue(current.type.replace('_', ' '))
        self.category_box.edit.setText(current.category)
        self.desc_box.currentWidget().set_current(current)

class TextDesc(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()

        self.header_box = PropertyBox("Header", QLineEdit, self)
        self.header_box.edit.textChanged.connect(self.header_changed)

        self.desc_box = PropertyBox("Description", QTextEdit, self)
        font_height = QFontMetrics(self.desc_box.edit.font())
        self.desc_box.edit.setFixedHeight(font_height.lineSpacing() * 20 + 20)
        self.desc_box.edit.textChanged.connect(self.desc_changed)

        self.layout.addWidget(self.header_box)
        self.layout.addWidget(self.desc_box)
        self.setLayout(self.layout)

    def header_changed(self, text=None):
        self.window.current.sub_nid = text

    def desc_changed(self, text=None):
        self.window.current.contrib = [[None, self.desc_box.edit.toPlainText()]]

    def set_current(self, current):
        try:
            self.header_box.edit.setText(current.sub_nid)
            self.desc_box.edit.setText(current.contrib[0][1])
        except: # spec isn't compatible
            pass

class PanoramaDesc(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()

        self.panorama_box = PropertyBox("Contribution", ComboBox, self)
        self.panorama_box.edit.addItem(QIcon(), 'None')
        for panorama in RESOURCES.panoramas:
            icon = QIcon(panorama.get_all_paths()[0])
            self.panorama_box.edit.addItem(icon, panorama.nid)
        self.panorama_box.edit.setIconSize(QSize(240, 160))
        self.panorama_box.edit.currentIndexChanged.connect(self.panorama_changed)

        self.contrib_box = PropertyBox("Name", QLineEdit, self)
        self.contrib_box.edit.textChanged.connect(self.contrib_changed)

        self.author_box = PropertyBox("Author", QLineEdit, self)
        self.author_box.edit.textChanged.connect(self.author_changed)

        self.layout.addWidget(self.panorama_box)
        self.layout.addWidget(self.contrib_box)
        self.layout.addWidget(self.author_box)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def panorama_changed(self, index):
        contrib = self.window.current.contrib
        sub_nid = self.panorama_box.edit.currentText()
        if not contrib or not len(contrib[0]) > 1 or \
            contrib[0][1] == self.window.current.sub_nid.replace('_', ' '):
                self.contrib_box.edit.setText(sub_nid.replace('_', ' '))
        self.window.current.sub_nid = sub_nid

    def contrib_changed(self, text):
        author = None
        contrib = self.window.current.contrib
        if contrib and contrib[0]:
            author = contrib[0][0]
        self.window.current.contrib = [[author, text]]

    def author_changed(self, text):
        desc = None
        contrib = self.window.current.contrib
        if contrib and len(contrib[0]) > 1:
            desc = contrib[0][1]
        self.window.current.contrib = [[text, desc]]

    def set_current(self, current):
        try:
            self.panorama_box.edit.setValue(current.sub_nid)
            self.contrib_box.edit.setText(current.contrib[0][1])
            self.author_box.edit.setText(current.contrib[0][0])
        except: # spec isn't compatible
            pass

class PushableIcon(PushableIcon16):
    display_width = 160

    def setType(self, type):
        self.type = type
        if type == '16x16_Icons':
            self.width, self.height = 16, 16
            self.database = RESOURCES.icons16
        elif type == '32x32_Icons':
            self.width, self.height = 32, 32
            self.database = RESOURCES.icons32
        elif type == '80x72_Icons':
            self.width, self.height = 80, 72
            self.database = RESOURCES.icons80
        elif type == 'Map_Icons':
            self.width, self.height = 48, 48
            self.database = RESOURCES.map_icons
        elif type == 'Portraits':
            self.width, self.height = 96, 80
            self.database = RESOURCES.portraits

    def onIconSourcePicker(self):
        if self.type == 'Portraits':
            from app.editor.portrait_editor import portrait_tab
            res, ok = portrait_tab.get()
        else:           
            from app.editor.icon_editor import icon_tab
            if self.type == 'Map_Icons':
                res, ok = icon_tab.get_map_icon_editor()
            else:
                res, ok = icon_tab.get(self.width, self._nid)

        if res and ok:
            icon_index = (0, 0)
            if self.type in ("16x16_Icons", "32x32_Icons", "80x72_Icons"):
                icon_index = res.icon_index

            self.change_icon(res.nid, icon_index)
            self.sourceChanged.emit(self._nid, self.x, self.y)

class IconDesc(QWidget):
    def __init__(self, parent=None, type='16x16_Icons'):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()       

        self.icon_box = PropertyBox("Contribution", PushableIcon, self)
        self.icon_box.edit.setType(type)
        self.icon_box.edit.sourceChanged.connect(self.on_icon_changed)

        self.contrib_box = PropertyBox("Name", QLineEdit, self)
        self.contrib_box.edit.textChanged.connect(self.contrib_changed)

        self.author_box = PropertyBox("Author", QLineEdit, self)
        self.author_box.edit.textChanged.connect(self.author_changed)

        self.layout.addWidget(self.icon_box)
        self.layout.addWidget(self.contrib_box)
        self.layout.addWidget(self.author_box)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def on_icon_changed(self, nid, x, y):
        contrib = self.window.current.contrib
        if not contrib or not len(contrib[0]) > 1 or \
            (self.window.current.sub_nid and contrib[0][1] == self.window.current.sub_nid.replace('_', ' ')):
                self.contrib_box.edit.setText(nid.replace('_', ' '))

        self.window.current.sub_nid = nid
        self.window.current.icon_index = (x, y)

    def contrib_changed(self, text):
        author = None
        contrib = self.window.current.contrib
        if contrib and contrib[0]:
            author = contrib[0][0]
        self.window.current.contrib = [[author, text]]

    def author_changed(self, text):
        desc = None
        contrib = self.window.current.contrib
        if contrib and len(contrib[0]) > 1:
            desc = contrib[0][1]
        self.window.current.contrib = [[text, desc]]

    def set_current(self, current):
        try:
            self.icon_box.edit.change_icon(current.sub_nid, current.icon_index)
            self.contrib_box.edit.setText(current.contrib[0][1])
            self.author_box.edit.setText(current.contrib[0][0])
        except:
            pass

class MapSpriteDesc(QWidget):
    display_width = 160

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()

        self.map_sprite_label = QLabel()
        self.map_sprite_box = QPushButton(("Choose Map Sprite..."))
        self.map_sprite_box.clicked.connect(self.select_map_sprite)

        self.author_box = PropertyBox("Author", QLineEdit, self)
        self.author_box.edit.textChanged.connect(self.author_changed)

        self.layout.addWidget(self.map_sprite_label)
        self.layout.addWidget(self.map_sprite_box)
        self.layout.addWidget(self.author_box)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def select_map_sprite(self):
        res, ok = map_sprite_tab.get()
        if ok:
            nid = res.nid
            self.window.current.sub_nid = nid
            pix = self.get_map_sprite_icon(self.window.current.sub_nid, num=0)
            self.map_sprite_label.setPixmap(pix)
            self.window.window.update_list()

    def author_changed(self, text):
        self.window.current.contrib = [[text, None]]

    def set_current(self, current):
        try:
            pix = self.get_map_sprite_icon(self.window.current.sub_nid, num=0)
            if pix:
                self.map_sprite_label.setPixmap(pix)
            else:
                self.map_sprite_label.clear()
            self.author_box.edit.setText(current.contrib[0][0])
        except: # spec isn't compatible
            pass

    def get_map_sprite_icon(self, nid, num, current=False, team='player', variant=None):
        res = None
        if variant and nid:
            res = RESOURCES.map_sprites.get(nid + variant)
        if nid and (not variant or not res):
            res = RESOURCES.map_sprites.get(nid)
        if not res:
            return None
        if not res.standing_pixmap:
            res.standing_pixmap = QPixmap(res.stand_full_path)
        pixmap = res.standing_pixmap
        pixmap = map_sprite_model.get_basic_icon(pixmap, num, current, team)
        pixmap = pixmap.scaled(self.display_width, self.display_width)
        return pixmap

class ListDesc(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()

        self.header_box = PropertyBox("Header", QLineEdit, self)
        self.header_box.edit.textChanged.connect(self.header_changed)

        attrs = ("Author", "Contribution")
        self.desc_box = AppendMultiListWidget([], "List of Contributions", attrs, KeyValueDelegate, self, model=KeyValueDoubleListModel)

        self.layout.addWidget(self.header_box)
        self.layout.addWidget(self.desc_box)
        self.setLayout(self.layout)

    def header_changed(self, text=None):
        self.window.current.sub_nid = text

    def set_current(self, current):
        try:
            self.header_box.edit.setText(current.sub_nid)
            self.desc_box.set_current(current.contrib)
        except: # spec isn't compatible
            pass