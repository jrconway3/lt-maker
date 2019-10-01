from functools import partial

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QToolButton, \
    QMessageBox, QSpinBox, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.database import DB
from app.data.weapons import WeaponType, WeaponRank

from app.editor.custom_gui import ComboBox
from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app.editor.icons import ItemIcon16
from app import utilities

class ItemDatabase(DatabaseDialog):
    @classmethod
    def create(cls, parent=None):
        data = DB.items
        title = "Items"
        right_frame = ItemProperties
        deletion_msg = ""
        creation_func = DB.create_new_item
        collection_model = ItemModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model, parent)
        return dialog

class ItemModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            item = self._data[index.row()]
            text = item.nid
            return text
        elif role == Qt.DecorationRole:
            item = self._data[index.row()]
            x, y = item.icon_index
            pixmap = QPixmap(item.icon_fn).copy(x*16, y*16, 16, 16)
            if pixmap.width() > 0 and pixmap.height() > 0:
                pixmap = pixmap.scaled(64, 64)
                return QIcon(pixmap)
            else:
                return None
        return None

class RangeBox(QWidget):
    # For now -- later when I add equations this will change
    def __init__(self, label, parent):
        super().__init__(parent)
        self.window = parent
        self.setMaximumWidth(160)

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        range_label = QLabel(label)
        self.edit = QSpinBox(self)
        self.valueChanged = self.edit.valueChanged
        self.edit.setRange(0, 15)
        self.edit.setMaximumWidth(40)

        hbox.addWidget(range_label)
        hbox.addWidget(self.edit)

    def setValue(self, val):
        self.edit.setValue(int(val))

    def setMinimum(self, val):
        self.edit.setMinimum(val)

    def setMaximum(self, val):
        self.edit.setMaximum(val)

class ComponentList(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.index_list = []

    def add_component(self, component):
        item = QListWidgetItem()
        item.setSizeHint(component.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, component)
        self.index_list.append(component.data.nid)
        return item

    def remove_component(self, component):
        if component.data.nid in self.index_list:
            idx = self.index_list.index(component.data.nid)
            self.index_list.remove(component.data.nid)
            return self.takeItem(idx)
        return None

class BoolItemComponent(QWidget):
    def __init__(self, data, parent):
        super().__init__(parent)
        self._data = data
        self.window = parent

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        name_label = QLabel(self._data.name)
        hbox.addWidget(name_label)

        self.create_editor(hbox)

        x_button = QToolButton(self)
        x_button.setIcon(QIcon("icons/x.png"))
        x_button.clicked.connect(partial(self.window.remove_component, self))
        hbox.addWidget(x_button, Qt.AlignRight)

    def create_editor(self, hbox):
        pass

    @property
    def data(self):
        return self._data
        
class IntItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QSpinBox(self)
        self.editor.setMaximumWidth(40)
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = val

class WeaponTypeItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_type in DB.weapons.values():
            self.editor.addItem(weapon_type.nid)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = DB.weapons.get(val)

class WeaponRankItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.values():
            self.editor.addItem(weapon_rank.nid)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = DB.weapon_ranks.get(val)

class ItemProperties(QWidget):
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
        self.nid_edit.textChanged.connect(self.nid_changed)
        self.nid_edit.editingFinished.connect(self.nid_done_editing)
        grid.addWidget(nid_label, 0, 2)
        grid.addWidget(self.nid_edit, 0, 3)

        name_label = QLabel('Display Name: ')
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(13)
        self.name_edit.textChanged.connect(self.name_changed)
        grid.addWidget(name_label, 1, 2)
        grid.addWidget(self.name_edit, 1, 3)

        value_label = QLabel("Value: ")
        self.value_edit = QSpinBox(self)
        self.value_edit.setMaximum(1000000)
        self.value_edit.valueChanged.connect(self.value_changed)
        grid.addWidget(value_label, 2, 2)
        grid.addWidget(self.value_edit, 2, 3)

        desc_label = QLabel("Description: ")
        self.desc_edit = QLineEdit(self)
        self.desc_edit.textChanged.connect(self.desc_changed)
        grid.addWidget(desc_label, 3, 0)
        grid.addWidget(self.desc_edit, 3, 1, 1, 3)

        self.min_range_edit = RangeBox("Min Range: ", self)
        self.min_range_edit.valueChanged.connect(self.min_range_changed)
        grid.addWidget(self.min_range_edit, 4, 0, 1, 2)

        self.max_range_edit = RangeBox("Max Range: ", self)
        self.max_range_edit.valueChanged.connect(self.max_range_changed)
        grid.addWidget(self.max_range_edit, 4, 2, 1, 2)

        component_label = QLabel("Item Components")
        grid.addWidget(component_label, 5, 0, 1, 3)

        self.add_component_button = QPushButton("Add...")
        self.add_component_button.setMaximumWidth(100)
        self.add_component_button.clicked.connect(self.search_components)
        grid.addWidget(self.add_component_button, 5, 3, Qt.AlignRight)

        self.component_list = ComponentList(self)
        if self.current:
            for component in self.current.components.values():
                self.add_component_widget(component)
        grid.addWidget(self.component_list, 6, 0, 1, 4)
            
        self.icon_edit = ItemIcon16(None, self)
        grid.addWidget(self.icon_edit, 0, 0, 2, 2)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Weapon Type ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def value_changed(self, val):
        self.current.value = int(val)

    def desc_changed(self, text):
        self.current.desc = text

    def min_range_changed(self, val):
        self.current.min_range = val
        # Max range can't be lower than min range
        self.max_range_edit.setMinimum(val)

    def max_range_changed(self, val):
        self.current.max_range = val
        self.min_range_edit.setMaximum(val)

    def add_component(self, component):
        self.add_component_widget(component)
        self.current.components.append(component)

    def add_component_widget(self, component):
        if component.attr == bool:
            c = BoolItemComponent(component, self)
        elif component.attr == int:
            c = IntItemComponent(component, self)
        elif component.attr == WeaponType:
            c = WeaponTypeItemComponent(component, self)
        elif component.attr == WeaponRank:
            c = WeaponRankItemComponent(component, self)
        elif type(component.attr) == tuple:  # TODO
            c = BoolItemComponent(component, self)
        else:  # TODO
            c = BoolItemComponent(component, self)
        self.component_list.add_component(c)

    def remove_component(self, component_widget):
        data = component_widget._data
        self.component_list.remove_component(component_widget)
        del self.current.components[data.nid]

    def set_current(self, current):
        self.current = current
        self.nid_edit.setText(current.nid)
        self.name_edit.setText(current.name)
        self.value_edit.setValue(current.value)
        self.desc_edit.setText(current.desc)
        self.min_range_edit.setValue(current.min_range)
        self.max_range_edit.setValue(current.max_range)
        self.icon_edit.set_current(current.icon_fn, current.icon_index)
        self.component_list.clear()
        for component in current.components.values():
            self.add_component_widget(component)

    def search_components(self):
        pass

# Testing
# Run "python -m app.editor.item_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ItemDatabase.create()
    window.show()
    app.exec_()
