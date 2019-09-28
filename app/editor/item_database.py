

class ItemDatabase(DatabaseDialog):
    @classmethod
    def create(cls, parent=None):
        data = DB.items
        title = "Items"
        right_frame = ItemProperties
        deletion_msg = ""
        creation_func = DB.create_new_item
        collection_model = ItemModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model)
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
            pixmap = QPixmap(item.icon_fn).copy(x*16, y*16, 16, 16).scaled(64, 64)
            return QIcon(pixmap)
        return None

class RangeBox(QWidget):
    # For now -- later when I add equations this will change
    def __init__(self, label, parent):
        super().__init__(parent)
        self.window = parent

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        range_label = QLabel(label)
        self.edit = QSpinbox(0, self)
        self.valueChanged = self.edit.valueChanged
        self.edit.setRange(0, 15)

        hbox.addWidget(range_label)
        hbox.addWidget(self.edit)

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
        self.value_edit = QSpinbox(self)
        self.value_edit.setMinimum(0)
        self.value_edit.valueChanged.connect(self.value_changed)
        grid.addWidget(value_label, 2, 2)
        grid.addWidget(self.value_edit, 2, 3)

        desc_label = QLabel("Description: ")
        self.desc_edit = QLineEdit(self)
        self.desc_edit.textChanged.connect(self.desc_changed)
        grid.addWidget(desc_label, 3, 0)
        grid.addWidget(self.desc_edit, 3, 1, 1, 3)

        self.min_range_edit = RangeBox("Min Range: ")
        self.min_range_edit.valueChanged.connect(self.min_range_changed)
        grid.addWidget(self.min_range_edit, 4, 0, 1, 2)

        self.max_range_edit = RangeBox("Max Range: ")
        self.max_range_edit.valueChanged.connect(self.max_range_changed)
        grid.addWidget(self.max_range_edit, 4, 2, 1, 2)

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
        self.max_range_edit.edit.setMinimum(val)

    def max_range_changed(self, val):
        self.current.max_range = val
        self.min_range_edit.edit.setMaximum(val)

    def set_current(self, current):
        self.current = current
        self.nid_edit.setText(current.nid)
        self.name_edit.setText(current.name)
        self.value_edit.setValue(current.value)
        self.desc_edit.setText(current.desc)
        self.min_range_edit.setValue(current.min_range)
        self.max_range_edit.setValue(current.max_range)
        self.icon_edit.set_current(current.icon_fn, current.icon_index)


# Testing
# Run "python -m app.editor.item_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ItemDatabase.create()
    window.show()
    app.exec_()
