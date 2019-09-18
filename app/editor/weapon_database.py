from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QCheckBox, QLineEdit, QPushButton, \
    QMessageBox, QDialog, QFileDialog, QSpinBox, QItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QDir, pyqtSignal

from app.data.database import DB
from app.data.weapons import AdvantageList

from app.editor.custom_gui import MultiAttrListModel, RightClickTreeView, ComboBox
from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app.editor.misc_dialogs import RankDialog
from app import utilities

class WeaponDatabase(DatabaseDialog):
    @classmethod
    def create(cls, parent=None):
        data = DB.weapons
        title = "Weapon Type"
        right_frame = WeaponProperties
        deletion_msg = "Cannot delete Default weapon type"
        creation_func = DB.create_new_weapon_type
        collection_model = WeaponModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model, parent)
        return dialog

class WeaponModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            weapon = self._data[index.row()]
            text = weapon.nid + " : " + weapon.name
            return text
        elif role == Qt.DecorationRole:
            weapon = self._data[index.row()]
            x, y = weapon.sprite_index
            pixmap = QPixmap(weapon.sprite_fn).copy(x*16, y*16, 16, 16).scaled(64, 64)
            return QIcon(pixmap)
        return None

class WeaponProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        grid = QGridLayout()
        self.setLayout(grid)

        self.current = current

        nid_label = QLabel('Unique ID: ')
        self.nid_edit = QLineEdit(self)
        self.nid_edit.setMaxLength(12)
        self.nid_edit.textChanged.connect(self.nid_changed)
        self.nid_edit.editingFinished.connect(self.nid_done_editing)
        grid.addWidget(nid_label, 0, 2, 1, 2)
        grid.addWidget(self.nid_edit, 0, 4, 1, 2)

        name_label = QLabel('Display Name: ')
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(12)
        self.name_edit.textChanged.connect(self.name_changed)
        grid.addWidget(name_label, 1, 2, 1, 2)
        grid.addWidget(self.name_edit, 1, 4, 1, 2)

        magic_label = QLabel("Magic:")
        self.magic_check = QCheckBox(self)
        self.magic_check.stateChanged.connect(self.magic_changed)
        grid.addWidget(magic_label, 2, 2)
        grid.addWidget(self.magic_check, 2, 3)

        self.rank_button = QPushButton("Edit Weapon Ranks...")
        self.rank_button = QPushButton("Edit Weapon Ranks...")
        self.rank_button.clicked.connect(self.edit_weapon_ranks)
        grid.addWidget(self.rank_button, 2, 4, 1, 2)

        self.advantage = AdvantageWidget(AdvantageList(), "Advantage versus:", self)
        grid.addWidget(self.advantage, 3, 0, 1, 6)

        self.disadvantage = AdvantageWidget(AdvantageList(), "Disadvantage versus:", self)
        grid.addWidget(self.disadvantage, 4, 0, 1, 6)

        self.icon_edit = ItemIcon(None, self)
        grid.addWidget(self.icon_edit, 0, 0, 3, 2)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Weapon Type ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_int(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def magic_changed(self, state):
        self.current.magic = bool(state)

    def edit_weapon_ranks(self):
        dlg = RankDialog.create()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            # Need to modify current weapon ranks here
            pass
        else:
            pass

    def set_current(self, current):
        self.current = current
        self.nid_edit.setText(current.nid)
        self.name_edit.setText(current.name)
        self.magic_check.setChecked(current.magic)
        self.advantage.set_current(current.advantage)
        self.disadvantage.set_current(current.disadvantage)
        self.icon_edit.set_current(current.sprite_fn, current.sprite_index)

class PushableIcon(QPushButton):
    sourceChanged = pyqtSignal(str)
    coordsChanged = pyqtSignal(int, int)
    width, height = 16, 16

    def __init__(self, fn, x, y, parent):
        super().__init__(parent)
        self.window = parent
        self._fn = fn
        self.x, self.y = x, y

        self.setMinimumHeight(64)
        self.setMaximumHeight(64)
        self.setMinimumWidth(64)
        self.setMaximumWidth(64)
        self.resize(64, 64)
        self.setStyleSheet("qproperty-iconSize: 64px;")
        self.change_icon_source(fn)
        self.pressed.connect(self.onIconSourcePicker)

    def render(self):
        if self._fn:
            big_pic = QPixmap(self._fn)
            pic = big_pic.copy(self.x*self.width, self.y*self.height, self.width, self.height)
            pic = pic.scaled(64, 64)
            pic = QIcon(pic)
            self.setIcon(pic)

    def get_size(self):
        im = QPixmap(self._fn)
        return im.width() // self.width, im.height() // self.height

    def change_icon_source(self, fn):
        if fn != self._fn:
            self._fn = fn
            # Check bounds
            max_width, max_height = self.get_size()
            if max_width >= self.x:
                self.x = max_width - 1  # Maximize
                self.coordsChanged.emit(self.x, self.y)
            if max_height >= self.y:
                self.y = max_height - 1  # Maximize
                self.coordsChanged.emit(self.x, self.y)
            self.sourceChanged.emit(fn)
        self.render()

    def change_icon_x(self, x):
        if x != self.x:
            self.x = x
            self.coordsChanged.emit(self.x, self.y)
        self.render()

    def change_icon_y(self, y):
        if y != self.y:
            self.y = y
            self.coordsChanged.emit(self.x, self.y)
        self.render()

    def onIconSourcePicker(self):
        starting_path = QDir.currentPath()
        fn, ok = QFileDialog.getOpenFileName(self, "Choose Sprite Sheet", starting_path,
                                             "PNG Files (*.png);;All Files(*)")
        if ok:
            self.change_icon_source(fn)

class ItemIcon(QWidget):
    width, height = 16, 16

    def __init__(self, source, parent):
        super().__init__(parent)
        self.window = parent

        grid = QGridLayout()
        self.setLayout(grid)

        self._fn = source
        self._x = 0
        self._y = 0

        self.icon = PushableIcon(self._fn, self._x, self._y, self)
        grid.addWidget(self.icon, 0, 0, 1, 4, Qt.AlignCenter)

        x_label = QLabel("X:")
        y_label = QLabel("Y:")
        grid.addWidget(x_label, 1, 0)
        grid.addWidget(y_label, 1, 2)

        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        grid.addWidget(self.x_spinbox, 1, 1)
        grid.addWidget(self.y_spinbox, 1, 3)

        self.set_spinbox_range()
        self.icon.sourceChanged.connect(self.on_source_changed)
        self.x_spinbox.valueChanged.connect(self.change_x)
        self.y_spinbox.valueChanged.connect(self.change_y)
        self.change_x(self._x)
        self.change_y(self._y)

    def set_current(self, fn, sprite_index):
        self._fn = fn
        self.icon.change_icon_source(self._fn)
        x, y = sprite_index
        self.change_x(x)
        self.change_y(y)
        self.set_spinbox_range()

    def change_x(self, value):
        self._x = value
        self.x_spinbox.setValue(self._x)
        self.icon.change_icon_x(value)
        if self.window.current:
            self.window.current.sprite_index = (self._x, self._y)
            self.window.window.update_list()

    def change_y(self, value):
        self._y = value
        self.y_spinbox.setValue(self._y)
        self.icon.change_icon_y(value)
        if self.window.current:
            self.window.current.sprite_index = (self._x, self._y)
            self.window.window.update_list()

    def on_source_changed(self, fn):
        self._fn = fn
        if self.window.current:
            self.window.current.sprite_fn = self._fn
            self.window.window.update_list()
        self.set_spinbox_range()

    def set_spinbox_range(self):
        max_width, max_height = self.icon.get_size()
        self.x_spinbox.setRange(0, max_width - 1)
        self.y_spinbox.setRange(0, max_height - 1)

class AdvantageWidget(QWidget):
    def __init__(self, advantage, title, parent):
        super().__init__(parent)
        self.window = parent

        self.current = advantage

        attrs = ('weapon_type', 'weapon_rank', 'damage', 'resist', 'accuracy', 'avoid', 'crit', 'dodge', 'attackspeed')
        self.model = MultiAttrListModel(self.current, attrs, None, self)
        self.view = RightClickTreeView(self)
        self.view.setModel(self.model)
        delegate = AdvantageDelegate(self.view)
        self.view.setItemDelegate(delegate)
        for col in range(9):
            self.view.resizeColumnToContents(col)

        layout = QGridLayout(self)
        layout.addWidget(self.view, 1, 0, 1, 2)
        self.setLayout(layout)

        label = QLabel(title)
        layout.addWidget(label, 0, 0)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self.model.add_new_row)
        layout.addWidget(add_button, 0, 1, alignment=Qt.AlignRight)

    def set_current(self, advantage):
        self.current = advantage
        self.model.set_new_data(self.current)

class AdvantageDelegate(QItemDelegate):
    type_column = 0
    rank_column = 1
    int_columns = (2, 3, 4, 5, 6, 7, 8)

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setRange(-255, 255)
            return editor
        elif index.column() == self.rank_column:
            editor = ComboBox(parent)
            for rank in DB.weapon_ranks:
                editor.addItem(rank.rank)
            editor.addItem("All")
            return editor
        elif index.column() == self.type_column:
            editor = ComboBox(parent)
            for weapon_type in DB.weapons:
                x, y = weapon_type.sprite_index
                icon = QPixmap(weapon_type.sprite_fn).copy(x*16, y*16, 16, 16)
                editor.addItem(QIcon(icon), weapon_type.nid)
            return editor
        else:
            return super().createEditor(parent, option, index)

# Testing
# Run "python -m app.editor.weapon_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = WeaponDatabase.create()
    window.show()
    app.exec_()
