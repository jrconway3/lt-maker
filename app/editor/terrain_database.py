from PyQt5.QtWidgets import QWidget, QSpacerItem, QPushButton, QDialog, \
    QLineEdit, QColorDialog, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QSizePolicy
from PyQt5.QtGui import QImage, QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal

from app.data.sprites import SPRITES
from app.data.database import DB

from app.editor.custom_gui import ComboBox, PropertyBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.mcost_dialog import McostDialog
from app import utilities

class TerrainDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.terrain
        title = "Terrain"
        right_frame = TerrainProperties

        def deletion_func(view, idx):
            return view.model().rowCount() > 1 

        deletion_criteria = (deletion_func, 'Cannot delete when only one terrain left!')
        collection_model = TerrainModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New " + self.title, nids)
        DB.create_new_terrain(nid, name)
        self.after_new()

class TerrainModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            terrain = self._data[index.row()]
            text = terrain.nid + " : " + terrain.name
            return text
        elif role == Qt.DecorationRole:
            terrain = self._data[index.row()]
            color = terrain.color
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(color[0], color[1], color[2]))
            return QIcon(pixmap)
        return None

class TerrainIcon(QPushButton):
    colorChanged = pyqtSignal(QColor)

    def __init__(self, color, parent):
        super().__init__(parent)
        self._color = None
        self.change_color(color)

        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self.setMinimumWidth(64)
        self.setMaximumWidth(64)
        self.resize(64, 64)
        self.pressed.connect(self.onColorPicker)

    def change_color(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(QColor(color))

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        dlg = QColorDialog()
        if self._color:
            dlg.setCurrentColor(QColor(self._color))
        if dlg.exec_():
            self.change_color(dlg.currentColor().name())

class TerrainProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.setStyleSheet("font: 10pt;")

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = TerrainIcon(QColor(0, 0, 0).name(), self)
        self.icon_edit.colorChanged.connect(self.on_color_change)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)
        self.name_box.edit.setMaxLength(13)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        top_section.addLayout(name_section)

        main_section = QVBoxLayout()

        self.minimap_box = PropertyBox("Minimap Type", ComboBox, self)
        minimap_tiles = QImage(DB.minimap.minimap_tiles)
        sf = DB.minimap.scale_factor
        for text, sprite_coord in DB.minimap.get_minimap_types():
            im = minimap_tiles.copy(sprite_coord[0]*sf, sprite_coord[1]*sf, sf, sf)
            icon = QIcon(QPixmap.fromImage(im).scaled(QSize(16, 16), Qt.KeepAspectRatio))
            self.minimap_box.edit.addItem(icon, text)
        self.minimap_box.edit.currentIndexChanged.connect(self.minimap_changed)

        self.platform_box = PropertyBox("Combat Platform Type", ComboBox, self)
        for text, sprite_name in DB.get_platform_types():
            icon = QIcon(SPRITES[sprite_name])
            self.platform_box.edit.addItem(icon, text)
        self.platform_box.edit.setIconSize(QSize(87, 40))
        self.platform_box.edit.currentIndexChanged.connect(self.platform_changed)

        movement_section = QHBoxLayout()
        self.movement_box = PropertyBox("Movement Type", ComboBox, self)
        self.movement_box.edit.addItems(DB.mcost.get_terrain_types())
        self.movement_box.edit.currentIndexChanged.connect(self.movement_changed)
        movement_section.addWidget(self.movement_box)

        self.movement_box.add_button(QPushButton('...'))
        self.movement_box.button.setMaximumWidth(40)
        self.movement_box.button.clicked.connect(self.access_movement_grid)

        main_section.addWidget(self.minimap_box)
        main_section.addWidget(self.platform_box)
        main_section.addLayout(movement_section)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.setAlignment(Qt.AlignTop)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [terrain.nid for terrain in DB.terrain.values() if terrain is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Terrain ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_int(self.current.nid, other_nids)
        DB.terrain.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def minimap_changed(self, index):
        self.current.minimap = self.minimap_box.edit.currentText()

    def platform_changed(self, index):
        self.current.platform = self.platform_box.edit.currentText()

    def movement_changed(self, index):
        self.current.movement = self.movement_box.edit.currentText()

    def access_movement_grid(self):
        dlg = McostDialog()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.movement_box.edit.clear()
            self.movement_box.edit.addItems(DB.mcost.get_terrain_types())
        else:
            pass

    def on_color_change(self, color):
        self.current.color = color.getRgb()
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.minimap_box.edit.setValue(current.minimap)
        self.platform_box.edit.setValue(current.platform)
        self.movement_box.edit.setValue(current.mtype)
        # Icon
        color = current.color
        self.icon_edit.change_color(QColor(color[0], color[1], color[2]).name())

# Testing
# Run "python -m app.editor.terrain_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TerrainDatabase.create()
    window.show()
    app.exec_()
