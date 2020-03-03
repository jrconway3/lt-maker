from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, \
    QSizePolicy, QTableView
from PyQt5.QtCore import Qt

from app.data.stats import StatList
from app.data.database import DB

from app.extensions.custom_gui import IntDelegate
from app.extensions.simple_list_models import VirtualListModel
from app.extensions.list_dialogs import MultiAttrListDialog
from app.editor.base_database_gui import MultiAttrCollectionModel

class StatListWidget(QWidget):
    def __init__(self, obj, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._obj = obj

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        column_titles = DB.stats.keys()
        if obj:
            row_titles = obj.get_stat_titles()
            row_values = obj.get_stat_lists()
        else:
            row_titles = ['Example']
            row_values = [StatList.from_xml([], DB.stats)]
        print(row_titles, row_values, flush=True)

        self.setup(column_titles, row_titles, row_values, title)

    def setup(self, column_titles, row_titles, row_values, title):
        self.model = StatModel(column_titles, row_titles, row_values, self)
        self.view = QTableView(self)
        self.view.setModel(self.model)
        delegate = IntDelegate(self.view, range(len(column_titles)))
        self.view.setItemDelegate(delegate)
        for col in range(len(column_titles)):
            self.view.resizeColumnToContents(col)

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, 1, 0, 1, 2)
        self.setLayout(layout)

        label = QLabel(title)
        label.setAlignment(Qt.AlignBottom)
        layout.addWidget(label, 0, 0)

        self.button = QPushButton("...")
        self.button.setMaximumWidth(40)
        layout.addWidget(self.button, 0, 1, alignment=Qt.AlignRight)

    def set_new_obj(self, obj):
        self._obj = obj
        row_titles = obj.get_stat_titles()
        row_values = obj.get_stat_lists()
        self.model.set_new_data(row_titles, row_values)
        for col in range(len(row_values[0])):
            self.view.resizeColumnToContents(col)

    def update_stats(self):
        column_titles = DB.stats.keys()
        self.model.update_column_header(column_titles)
        if self._obj:
            self.set_new_obj(self._obj)

class StatModel(VirtualListModel):
    def __init__(self, columns, rows, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self._rows = rows
        self._data: list = data  # Must be list of StatLists

    def set_new_data(self, stat_titles: list, stat_lists: list):
        self._rows: list = stat_titles
        self._data: list = stat_lists
        self.layoutChanged.emit()

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            val = self._rows[idx]
            return val
        elif orientation == Qt.Horizontal:
            return self._columns[idx]

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = self._data[index.row()]  # row is a StatList
            key = self._columns[index.column()]
            val = row.get(key).value
            return val
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        row = self._data[index.row()]  # A StatList
        key = self._columns[index.column()]  # A stat key
        stat = row.get(key)
        stat.value = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
        return basic_flags

class StatTypeMultiModel(MultiAttrCollectionModel):
    def delete(self, idx):
        element = DB.stats[idx]
        # all clases and units are automatically affected!
        # But not all equations are automatically effected
        # But we will just let equations check themselves!!!
        # Also some item components can use stat lists!!!
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.remove_key(element.nid)
        for unit in DB.units:
            for row in unit.get_stat_lists():
                row.remove_key(element.nid)
        super().delete(idx)

    def create_new(self):
        return self._data.add_new_default(DB)

    def change_watchers(self, data, attr, old_value, new_value):
        if attr == 'nid':
            for klass in DB.classes:
                for row in klass.get_stat_lists():
                    row.change_key(old_value, new_value)
            for unit in DB.classes:
                for row in unit.get_stat_lists():
                    row.change_key(old_value, new_value)
            for equation in DB.equations:
                equation.expression.replace(old_value, new_value)
        elif attr == 'maximum':
            for klass in DB.classes:
                for row in klass.get_stat_lists():
                    row.set_maximum(data.nid, new_value)
            for unit in DB.classes:
                for row in unit.get_stat_lists():
                    row.set_maximum(data.nid, new_value)

    def update_watchers(self, idx):
        for klass in DB.classes:
            for row in klass.get_stat_lists():
                row.new_key(DB.stats[idx].nid)
        for unit in DB.classes:
            for row in unit.get_stat_lists():
                row.new_key(DB.stats[idx].nid)

class StatTypeDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        def deletion_func(view, idx):
            return view.window._data[idx].nid not in ("HP", "MOV")

        deletion_criteria = (deletion_func, "Cannot delete HP or MOV stats!")
        return cls(DB.stats, "Stat", ("nid", "name", "maximum", "desc"),
                   StatTypeMultiModel, deletion_criteria, {"HP", "MOV"})
