from PyQt5.QtWidgets import QWidget, QGridLayout, QListView, QPushButton, QDialog, \
    QFormLayout, QLineEdit, QDialogButtonBox, QLabel, QColorDialog, QHBoxLayout, \
    QMessageBox
from PyQt5.QtGui import QImage, QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QAbstractListModel, QSize, pyqtSignal

from app.data.sprites import SPRITES
from app.data.database import DB

from app.editor.custom_gui import ComboBox
from app.editor.mcost_dialog import McostDialog
import app.utilities as utilities

class TerrainMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.setWindowTitle('Terrain Editor')

        self.saved_data = self.save()

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.left_frame = Collection(self)
        self.right_frame = TerrainProperties(self)
        self.left_frame.set_display(self.right_frame)

        self.grid.addWidget(self.left_frame, 0, 0)
        self.grid.addWidget(self.right_frame, 0, 1)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

    def update_list(self):
        self.left_frame.update_list()

    def save(self):
        return DB.terrain.serialize()

    def restore(self, data):
        DB.terrain.restore(data)

    def apply(self):
        self.saved_data = self.save()

    def accept(self):
        super().accept()

    def reject(self):
        self.restore(self.saved_data)
        super().reject()

class Collection(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window
        self.display = None  # Partner that displays additional information about this collection

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.list_view = QListView(self)
        # self.list_view.setMinimumSize(128, 240)
        self.list_view.uniformItemSizes = True
        self.list_view.currentChanged = self.on_item_changed

        self.model = TerrainDictModel(self)
        self.list_view.setModel(self.model)
        self.list_view.setIconSize(QSize(32, 32))

        self.button = QPushButton("Create New Terrain Type...")
        self.button.clicked.connect(self.create_new_terrain_type)

        self.grid.addWidget(self.list_view, 0, 0)
        self.grid.addWidget(self.button, 1, 0)

        # first_index = self.model.index(0, 0)
        # self.list_view.setCurrentIndex(first_index)

    def create_new_terrain_type(self):
        dialog = NewTerrainDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            nid, name = dialog.get_results()
            DB.terrain.add_new(nid, name)
            # self.model.dataChanged.emit()
            self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(self.model.rowCount(), 0))
            last_index = self.model.index(self.model.rowCount() - 1, 0)
            self.list_view.setCurrentIndex(last_index)

    def on_item_changed(self, curr, prev):
        new_terrain = list(DB.terrain.values())[curr.row()]
        if self.display:
            self.display.set_current(new_terrain)

    def set_display(self, disp):
        self.display = disp
        first_index = self.model.index(0, 0)
        self.list_view.setCurrentIndex(first_index)

    def update_list(self):
        self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(self.model.rowCount(), 0))
        # self.model.dataChanged.emit()

class TerrainDictModel(QAbstractListModel):
    def __init__(self, window=None):
        super().__init__(window)
        self._data = DB.terrain

    def rowCount(self, parent=None):
        return len(self._data)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            terrain = list(self._data.values())[index.row()]
            text = terrain.nid + " : " + terrain.name
            return text
        elif role == Qt.DecorationRole:
            terrain = list(self._data.values())[index.row()]
            color = terrain.color
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(color[0], color[1], color[2]))
            return QIcon(pixmap)
        return None

class NewTerrainDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.menu = parent
        self.setWindowTitle("Create New Terrain...")

        self.form = QFormLayout(self)
        self.name = QLineEdit(self)
        self.nid = QLineEdit(self)
        self.nid.textChanged.connect(self.nid_changed)
        self.warning_message = QLabel('')
        self.warning_message.setStyleSheet("QLabel { color : red; }")
        self.form.addRow('Display Name: ', self.name)
        self.form.addRow('Internal ID: ', self.nid)
        self.form.addRow(self.warning_message)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.form.addRow(self.buttonbox)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        # No level id set
        accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
        accept_button.setEnabled(False)
        self.warning_message.setText('No Terrain ID set.')

    def nid_changed(self, text):
        if text in DB.terrain.keys():
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('Terrain ID is already in use.')
        elif text:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(True)
            self.warning_message.setText('')
        else:
            accept_button = self.buttonbox.button(QDialogButtonBox.Ok)
            accept_button.setEnabled(False)
            self.warning_message.setText('No Terrain ID set.')

    def get_results(self):
        title = self.name.text()
        nid = self.nid.text()
        return title, nid

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
        self.database_editor = self.window.window

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.current = current

        nid_label = QLabel('Unique ID: ')
        self.nid_edit = QLineEdit(self)
        self.nid_edit.setMaxLength(12)
        self.nid_edit.textChanged.connect(self.nid_changed)
        self.nid_edit.editingFinished.connect(self.nid_done_editing)
        self.grid.addWidget(nid_label, 0, 1)
        self.grid.addWidget(self.nid_edit, 0, 2)

        name_label = QLabel('Display Name: ')
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(12)
        self.name_edit.textChanged.connect(self.name_changed)
        self.grid.addWidget(name_label, 1, 1)
        self.grid.addWidget(self.name_edit, 1, 2)

        minimap_label = QLabel('Minimap Type: ')
        self.minimap_edit = ComboBox(self)
        minimap_tiles = QImage(DB.minimap.minimap_tiles)
        sf = DB.minimap.scale_factor
        for text, sprite_coord in DB.minimap.get_minimap_types():
            im = minimap_tiles.copy(sprite_coord[0]*sf, sprite_coord[1]*sf, sf, sf)
            icon = QIcon(QPixmap.fromImage(im).scaled(QSize(16, 16), Qt.KeepAspectRatio))
            self.minimap_edit.addItem(icon, text)
        self.minimap_edit.currentIndexChanged.connect(self.minimap_changed)
        self.grid.addWidget(minimap_label, 2, 0)
        self.grid.addWidget(self.minimap_edit, 2, 1, 1, 2)

        platform_label = QLabel('Combat Platform Type: ')
        self.platform_edit = ComboBox(self)
        for text, sprite_name in DB.get_platform_types():
            icon = QIcon(SPRITES[sprite_name])
            self.platform_edit.addItem(icon, text)
        self.platform_edit.setIconSize(QSize(87, 40))
        self.platform_edit.currentIndexChanged.connect(self.platform_changed)
        self.grid.addWidget(platform_label, 3, 0)
        self.grid.addWidget(self.platform_edit, 3, 1, 1, 2)

        movement_box = QHBoxLayout()
        movement_label = QLabel('Movement Type: ')
        self.movement_edit = ComboBox(self)
        self.movement_edit.addItems(DB.mcost.get_terrain_types())
        self.movement_edit.currentIndexChanged.connect(self.movement_changed)
        self.movement_info = QPushButton('...')
        self.movement_info.setMaximumWidth(40)
        self.movement_info.clicked.connect(self.access_movement_grid)
        self.grid.addWidget(movement_label, 4, 0)
        movement_box.addWidget(self.movement_edit)
        movement_box.addWidget(self.movement_info)
        self.grid.addLayout(movement_box, 4, 1, 1, 2)

        self.icon_edit = TerrainIcon(QColor(0, 0, 0).name(), self)
        self.icon_edit.colorChanged.connect(self.on_color_change)
        self.grid.addWidget(self.icon_edit, 0, 0, 2, 1)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        nids = [_.nid for _ in DB.terrain.values()]
        if self.current.nid in nids:
            QMessageBox.warning(self.window, 'Warning', 'Terrain ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_int(self.current.nid, nids)
        my_key = None
        for key, value in DB.terrain.items():
            if value.nid == self.current.nid:
                my_key = key
                break
        if my_key:
            DB.terrain[self.current.nid] = DB.terrain.pop(my_key)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def minimap_changed(self, index):
        self.current.minimap = self.minimap_edit.currentText()

    def platform_changed(self, index):
        self.current.platform = self.platform_edit.currentText()

    def movement_changed(self, index):
        self.current.movement = self.movement_edit.currentText()

    def access_movement_grid(self):
        dlg = McostDialog()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.movement_edit.clear()
            self.movement_edit.addItems(DB.mcost.get_terrain_types())
        else:
            pass

    def on_color_change(self, color):
        self.current.color = color.getRgb()
        self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_edit.setText(current.nid)
        self.name_edit.setText(current.name)
        self.minimap_edit.setValue(current.minimap)
        self.platform_edit.setValue(current.platform)
        self.movement_edit.setValue(current.mtype)
        # Icon
        color = current.color
        self.icon_edit.change_color(QColor(color[0], color[1], color[2]).name())

# Testing
# Run "python -m app.editor.terrain_menu" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TerrainMenu()
    window.show()
    app.exec_()
