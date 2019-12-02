from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, \
    QDialog, QVBoxLayout, QSizePolicy, QSpacerItem, QComboBox, QStyledItemDelegate
from PyQt5.QtCore import Qt

from app.data.database import DB
import app.data.item_components as IC

from app.editor.custom_gui import get_icon, PropertyBox, QHLine, ComboBox, RightClickListView, SingleListModel
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.misc_dialogs import EquationDialog
from app.editor.icons import ItemIcon16
from app.editor import component_database
from app import utilities

class ItemDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.items
        title = "Item"
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
            return get_icon(item, scale_to=2)
        return None

class ItemProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon16(None, self)
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

        main_section = QGridLayout()

        self.desc_box = PropertyBox("Description", QLineEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)
        main_section.addWidget(self.desc_box, 0, 0, 1, 3)

        self.value_box = PropertyBox("Value", QSpinBox, self)
        self.value_box.edit.setMaximum(1000000)
        self.value_box.edit.valueChanged.connect(self.value_changed)
        main_section.addWidget(self.value_box, 1, 0)

        self.min_range_box = PropertyBox("Minimum Range", ComboBox, self)
        self.min_range_box.edit.setEditable(True)
        self.min_range_box.edit.setInsertPolicy(QComboBox.NoInsert)
        self.min_range_box.edit.addItems(DB.equations.keys())
        # self.min_range_box.edit.currentTextChanged.connect(self.min_range_changed)
        self.min_range_box.edit.lineEdit().editingFinished.connect(self.check_min_range)
        main_section.addWidget(self.min_range_box, 1, 1)

        self.min_range_box.add_button(QPushButton('...'))
        self.min_range_box.button.setMaximumWidth(40)
        self.min_range_box.button.clicked.connect(self.access_equations)

        self.max_range_box = PropertyBox("Maximum Range", ComboBox, self)
        self.max_range_box.edit.setEditable(True)
        self.max_range_box.edit.setInsertPolicy(QComboBox.NoInsert)
        self.max_range_box.edit.addItems(DB.equations.keys())
        # self.max_range_box.edit.currentTextChanged.connect(self.max_range_changed)
        self.max_range_box.edit.lineEdit().editingFinished.connect(self.check_max_range)
        main_section.addWidget(self.max_range_box, 1, 2)

        self.max_range_box.add_button(QPushButton('...'))
        self.max_range_box.button.setMaximumWidth(40)
        self.max_range_box.button.clicked.connect(self.access_equations)

        component_section = QGridLayout()
        component_label = QLabel("Components")
        component_label.setAlignment(Qt.AlignBottom)
        component_section.addWidget(component_label, 0, 0, Qt.AlignBottom)

        self.add_component_button = QPushButton("Add Components...")
        self.add_component_button.clicked.connect(self.add_components)
        component_section.addWidget(self.add_component_button, 0, 1)

        self.component_list = component_database.ComponentList(self)
        component_section.addWidget(self.component_list, 1, 0, 1, 2)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        h_line = QHLine()
        total_section.addWidget(h_line)
        total_section.addLayout(component_section)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Item Type ID %s already in use' % self.current.nid)
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

    def check_min_range(self):
        min_val = self.min_range_box.edit.currentText()
        self.current.min_range = min_val
        max_val = self.max_range_box.edit.currentText()
        # Max range can't be lower than min range
        if utilities.is_int(min_val) and utilities.is_int(max_val):
            if min_val > max_val:
                self.max_range_box.edit.setEditText(str(min_val))

    def check_max_range(self):
        max_val = self.max_range_box.edit.currentText()
        self.current.max_range = max_val
        min_val = self.min_range_box.edit.currentText()
        # Min range can't be higher than max range
        if utilities.is_int(min_val) and utilities.is_int(max_val):
            if max_val < min_val:
                self.min_range_box.edit.setEditText(str(max_val))

    def min_range_changed(self, val):
        self.current.min_range = val

    def max_range_changed(self, val):
        self.current.max_range = val

    def access_equations(self):
        dlg = EquationDialog.create()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.min_range_box.edit.clear()
            self.min_range_box.edit.addItems(DB.equations.keys())
            self.max_range_box.edit.clear()
            self.max_range_box.edit.addItems(DB.equations.keys())
        else:
            pass

    def add_component(self, component):
        self.add_component_widget(component)
        self.current.components.append(component)

    def add_component_widget(self, component):
        c = component_database.get_display_widget(component, self)
        self.component_list.add_component(c)

    def remove_component(self, component_widget):
        data = component_widget._data
        self.component_list.remove_component(component_widget)
        self.current.components.delete(data)

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.value_box.edit.setValue(current.value)
        self.desc_box.edit.setText(current.desc)
        if utilities.is_int(current.min_range):
            self.min_range_box.edit.setEditText(current.min_range)
        else:
            self.min_range_box.edit.setValue(current.min_range)
        if utilities.is_int(current.max_range):
            self.max_range_box.edit.setEditText(current.max_range)
        else:
            self.max_range_box.edit.setValue(current.max_range)
        self.icon_edit.set_current(current.icon_fn, current.icon_index)
        self.component_list.clear()
        for component in current.components.values():
            self.add_component_widget(component)

    def add_components(self):
        dlg = component_database.ComponentDialog(IC.item_components, "Item Components", self)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            checked = dlg.get_checked()
            for nid in checked:
                c = IC.get_component(nid)
                self.add_component(c)
        else:
            pass

class ItemList(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.index_list = []
        self.combo_box_list = []

    def add_item(self, item):
        new_box = QListWidgetItem()
        combo_box = ComboBox(self)
        for i in DB.items:
            combo_box.addItem(get_icon(i), i.nid)
        combo_box.setValue(item.nid)
        self.addItem(new_box)
        self.setItemWidget(new_box, combo_box)
        self.index_list.append(item.nid)
        self.combo_box_list.append(combo_box)
        return item

    def remove_item(self, item):
        if item.nid in self.index_list:
            idx = self.index_list.index(item.nid)
            self.index_list.remove(item.nid)
            self.combo_box_list.pop(idx)
            return self.takeItem(idx)
        return None

    def clear(self):
        super().clear()
        self.index_list.clear()
        self.combo_box_list.clear()

class ItemListDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = ComboBox(parent)
        for item in DB.items:
            editor.addItem(get_icon(item), item.nid)
        return editor

    def setEditorData(self, editor, index):
        currentText = index.data(Qt.EditRole)
        editor.setValue(currentText)
        editor.showPopup()

    def setModelData(self, editor, model, index):
        current_nid = editor.currentText()
        current_item = DB.items.get(current_nid)
        model.setData(index, current_item, Qt.EditRole)

class ItemListWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._actions = []
        self.model = ItemListModel([], 'Item', self)
        self.view = RightClickListView(self)
        self.view.setModel(self.model)
        delegate = ItemListDelegate(self.view)
        self.view.setItemDelegate(delegate)

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.view, 1, 0, 1, 2)
        self.setLayout(self.layout)

        label = QLabel(title)
        label.setAlignment(Qt.AlignBottom)
        self.layout.addWidget(label, 0, 0)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self.model.add_new_row)
        self.layout.addWidget(add_button, 0, 1, alignment=Qt.AlignRight)

    def set_current(self, items):
        self.model.set_new_data(items)

class ItemListModel(SingleListModel):
    def add_new_row(self):
        new_row = DB.items[0]
        self.window._actions.append(('Append', new_row))
        self._data.append(new_row)
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1, 0)
        self.window.view.setCurrentIndex(last_index)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            item = self._data[index.row()]
            return item.nid
        elif role == Qt.DecorationRole:
            item = self._data[index.row()]
            return get_icon(item)
        return None

# Testing
# Run "python -m app.editor.item_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ItemDatabase.create()
    window.show()
    app.exec_()
