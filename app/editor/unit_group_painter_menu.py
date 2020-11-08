from PyQt5.QtWidgets import QPushButton, QLineEdit, \
    QWidget, QDialog, QVBoxLayout, QMessageBox, QListWidgetItem, \
    QGridLayout
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor

from app.utilities import str_utils
from app.utilities.data import Data

from app.editor import timer

from app.extensions.widget_list import WidgetList
from app.extensions.custom_gui import Dialog, RightClickListView, QHLine
from app.editor.custom_widgets import ObjBox
from app.editor.unit_painter_menu import AllUnitModel, InventoryDelegate

from app.data.level_units import UnitGroup

class UnitGroupMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.main_editor = self.window
        self.map_view = self.main_editor.map_view
        if self.current_level:
            self._data = self.current_level.unit_groups
        else:
            self._data = Data()

        grid = QVBoxLayout()
        self.setLayout(grid)

        self.group_list = GroupList(self)
        for group in self._data:
            self.group_list.add_group(group)
        grid.addWidget(self.group_list)

        self.create_button = QPushButton("Create New Group")
        self.create_button.clicked.connect(self.create_new_group)
        grid.addWidget(self.create_button)

    @property
    def current_level(self):
        return self.window.current_level

    def create_new_group(self):
        nid = str_utils.get_next_name('New Group', self._data.keys())
        new_group = UnitGroup(nid, Data(), [])
        self._data.append(new_group)
        self.group_list.add_group(new_group)

    def on_visibility_changed(self, state):
        pass

    def get_current(self):
        for index in self.group_list.selectedIndexes():
            idx = index.row()
            if len(self._data) > 0 and idx < len(self._data):
                return self._data[idx]
        return None

class GroupList(WidgetList):
    def add_group(self, group):
        item = QListWidgetItem()
        group_widget = GroupWidget(group, self.parent())
        item.setSizeHint(group_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, group_widget)
        self.index_list.append(group.nid)
        return item

    def remove_group(self, group):
        if group.nid in self.index_list:
            idx = self.index_list.index(group.nid)
            self.index_list.remove(group.nid)
            return self.takeItem(idx)
        return None

class GroupWidget(QWidget):
    def __init__(self, group, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = group

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.nid_box = QLineEdit(self)
        self.layout.addWidget(self.nid_box, 0, 0)

        hline = QHLine()
        self.layout.addWidget(hline, 1, 0, 1, 2)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self.add_new_unit)
        self.layout.addWidget(add_button, 0, 1, alignment=Qt.AlignRight)

        def false_func(model, index):
            return False

        self.view = RightClickListView((None, false_func, false_func), parent=self)
        self.view.currentChanged = self.on_item_changed

        self.model = GroupUnitModel(Data(), self)
        self.model.positions = {}
        self.view.setModel(self.model)
        self.view.setIconSize(QSize(32, 32))
        self.inventory_delegate = InventoryDelegate(Data())
        self.view.setItemDelegate(self.inventory_delegate)

        self.layout.addWidget(self.view, 3, 0, 1, 2)

        timer.get_timer().tick_elapsed.connect(self.tick)

        self.set_current(self._data)

    def tick(self):
        self.model.layoutChanged.emit()

    @property
    def current_level(self):
        return self.window.current_level

    def on_item_changed(self, curr, prev):
        pass

    def set_current(self, group):
        self._data = group
        self.model._data = self._data.units
        self.model.positions = self._data.positions
        self.model.update()
        self.inventory_delegate._data = self._data.units

    def select(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def deselect(self):
        self.view.clearSelection()

    def add_new_unit(self):
        unit_nid, ok = SelectUnitDialog.get_unit_nid(self)
        if ok:
            if unit_nid in self._data.units.keys():
                QMessageBox.critical(self, "Error!", "%s already present in group!" % unit_nid)
            else:
                unit = self.current_level.units.get(unit_nid)
                print(unit_nid, unit)
                print(self.current_level.units)
                self._data.units.append(unit)

class SelectUnitDialog(Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Unit")
        self.window = parent
        self.view = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.unit_box = ObjBox("Units", AllUnitModel, self.window.current_level.units, self)
        self.unit_box.edit.setIconSize(QSize(32, 32))
        self.unit_box.edit.view().setUniformItemSizes(True)
        self.view = self.unit_box.edit.view()

        layout.addWidget(self.unit_box)
        layout.addWidget(self.buttonbox)

    @classmethod
    def get_unit_nid(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.unit_box.edit.currentIndex()
            unit_nid = dialog.window.current_level.units[idx].nid
            return unit_nid, True
        else:
            return None, False

class GroupUnitModel(AllUnitModel):
    def data(self, index, role):
        if role == Qt.ForegroundRole:
            unit = self._data[index.row()]
            if unit.nid in self.positions:
                return QBrush()
            else:
                return QBrush(QColor("red"))
        else:
            return super().data(index, role)
        return None
