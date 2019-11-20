from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, \
    QSizePolicy, QTableView
from PyQt5.QtCore import Qt

from app.data.stats import StatList
from app.data.database import DB

from app.editor.custom_gui import IntDelegate, VirtualListModel

class ClassStatWidget(QWidget):
    def __init__(self, obj, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._obj = obj

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        column_titles = DB.stats.keys()
        row_titles = ['Generic Bases', 'Generic Growths', 'Promotion Gains', 'Growth Bonuses', 'Stat Maximums']
        if obj:
            row_values = obj.get_stat_lists()
        else:
            row_values = [StatList([], DB.stats)] * 5

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
        row_values = obj.get_stat_lists()
        self.model.set_new_data(row_values)
        for col in range(len(row_values[0])):
            self.view.resizeColumnToContents(col)

    def update_stats(self):
        column_titles = DB.stats.keys()
        self.model.update_column_header(column_titles)
        self.set_new_obj(self._obj)

class UnitStatWidget(ClassStatWidget):
    def __init__(self, obj, title, parent=None):
        super().__init__(parent)
        self.window = parent
        self._unit = obj

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        column_titles = DB.stats.keys()
        row_titles = ['Personal Bases', 'Personal Growths']
        if obj:
            row_values = obj.get_stat_lists()
        else:
            row_values = [StatList([], DB.stats)] * 2

        self.setup(column_titles, row_titles, row_values, title)

class StatModel(VirtualListModel):
    def __init__(self, columns, rows, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self._rows = rows
        self._data: list = data  # Must be list of StatLists

    def set_new_data(self, stat_lists: list):
        self._data: list = stat_lists
        self.layoutChanged.emit()

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        with open('wow.txt', 'a') as fp:
            fp.write(str(idx) + ' ' + str(orientation) + '\n')
        if orientation == Qt.Vertical:
            val = self._rows[idx]
            return val
        elif orientation == Qt.Horizontal:
            return self._columns[idx]

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = self._data[index.row()]  # A StatList
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
