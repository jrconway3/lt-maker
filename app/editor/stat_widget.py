import math

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, \
    QSizePolicy, QTableView, QPushButton, QDialog, QHBoxLayout, \
    QButtonGroup
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.data.stats import StatList
from app.data.database import DB

from app.extensions.custom_gui import IntDelegate
from app.extensions.list_models import VirtualListModel

class MultiEditTableView(QTableView):
    def commitData(self, editor):
        super().commitData(editor)
        model = self.currentIndex().model()
        value = model.data(self.currentIndex(), Qt.EditRole)
        for index in self.selectionModel().selectedIndexes():
            model.setData(index, value, Qt.EditRole)

class StatListWidget(QWidget):
    def __init__(self, obj, title, reset_button=False, parent=None):
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
            row_values = [StatList.default(DB)]

        self.reset_button_flag = reset_button

        self.setup(column_titles, row_titles, row_values, title)

    def setup(self, column_titles, row_titles, row_values, title):
        self.model = StatModel(column_titles, row_titles, row_values, self)
        self.view = MultiEditTableView(self)
        self.view.setModel(self.model)
        self.view.setSelectionMode(3)  # ExtendedSelection
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

        hbox = QHBoxLayout()

        if self.reset_button_flag:
            self.reset_button = QPushButton("Apply Class Values")
            self.reset_button.setMaximumWidth(150)
            hbox.addWidget(self.reset_button, alignment=Qt.AlignRight)

        self.button = QPushButton("Display Averages")
        self.button.setMaximumWidth(130)
        hbox.addWidget(self.button, alignment=Qt.AlignRight)
        layout.addLayout(hbox, 0, 1, alignment=Qt.AlignRight)

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

class StatAverageDialog(QDialog):
    def __init__(self, current, title, model, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle("%s Stat Averages Display" % title)
        self.window = parent
        self.current = current

        column_titles = DB.stats.keys()
        self.setup(column_titles, "Average Stats", model)
        if title == 'Generic':
            self.view.verticalHeader().setFixedWidth(20)  

    def setup(self, column_titles, title, model):
        self.model = model(column_titles, self.current, parent=self)
        self.view = QTableView(self)
        self.view.setModel(self.model)
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

        hbox_layout = QHBoxLayout()
        hbox_layout.setSpacing(0)
        hbox_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(hbox_layout, 0, 1, alignment=Qt.AlignRight)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.buttonToggled.connect(self.button_clicked)
        self.button10 = QPushButton("10%")
        self.button50 = QPushButton("50%")
        self.button90 = QPushButton("90%")
        self.buttons = [self.button10, self.button50, self.button90]
        for idx, button in enumerate(self.buttons):
            button.setMaximumWidth(50)
            button.setCheckable(True)
            hbox_layout.addWidget(button, alignment=Qt.AlignRight)
            self.button_group.addButton(button)
            self.button_group.setId(button, idx)
        self.button50.setChecked(True)

    def button_clicked(self, spec_button):
        checked = spec_button.isChecked()
        if checked:
            if spec_button == self.button10:
                self.model.average_idx = 2
            elif spec_button == self.button50:
                self.model.average_idx = 1
            elif spec_button == self.button90:
                self.model.average_idx = 3
            self.update()

    def set_current(self, current):
        self.current = current
        self.model.set_current(self.current)

    def update(self):
        self.model.layoutChanged.emit()

    def closeEvent(self, event):
        # Remove averages dialog
        self.window.averages_dialog = None

class Binomial():
    @staticmethod
    def fact(n, k):
        return math.factorial(n) / math.factorial(k) / math.factorial(n - k)

    @staticmethod
    def binom(x, n, p):
        return Binomial.fact(n, x) * p**x * (1-p)**(n-x)

    @staticmethod
    def cdf(x, n, p):
        total = 0
        for i in range(x + 1):
            total += Binomial.binom(i, n, p)
        return total

    @staticmethod
    def quantile(q, n, p):
        for x in range(n + 1):
            prob = Binomial.cdf(x, n, p)
            if prob > q:
                return x
        return n

class ClassStatAveragesModel(VirtualListModel):
    average_idx = 1

    def __init__(self, columns, current, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self.current = current  
        self._rows = [1] + list(range(5, current.max_level, 5)) + [current.max_level]

    def set_current(self, current):
        self.current = current
        self._rows = [1] + list(range(5, current.max_level, 5)) + [current.max_level]
        self.layoutChanged.emit()

    def determine_average(self, obj, stat_nid, level_ups):
        stat_base = obj.bases.get(stat_nid).value
        stat_growth = obj.growths.get(stat_nid).value
        stat_max = obj.max_stats.get(stat_nid).value

        average = int(stat_base + 0.5 + (stat_growth/100) * level_ups)

        # average = quantile(.5, level_ups, stat_growth/100) + stat_base
        quantile10 = Binomial.quantile(.1, level_ups, stat_growth/100) + stat_base
        quantile90 = Binomial.quantile(.9, level_ups, stat_growth/100) + stat_base
        return stat_max, average, quantile10, quantile90

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def rowCount(self, parent=None):
        return len(self._rows)

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            val = self._rows[idx]
            return val
        elif orientation == Qt.Horizontal:
            return self._columns[idx]

    def get_data(self, index):
        level = self._rows[index.row()]
        stat_nid = self._columns[index.column()]
        vals = self.determine_average(self.current, stat_nid, level - 1)
        avg = vals[self.average_idx]
        maxim = vals[0]
        return maxim, avg

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            maxim, avg = self.get_data(index)
            return min(maxim, avg)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter
        elif role == Qt.FontRole:
            maxim, avg = self.get_data(index)
            font = QFont()
            if avg >= maxim:
                font.setBold(True)
            return font

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren
        return basic_flags

class GenericStatAveragesModel(ClassStatAveragesModel):
    def __init__(self, columns, current, parent=None):
        VirtualListModel.__init__(self, parent)
        self.window = parent
        self._columns = self._headers = columns
        self.current = current  
        self._rows = [current.level]

    def set_current(self, current):
        self.current = current
        self._rows = [current.level]
        self.layoutChanged.emit()

    def determine_average(self, obj, stat_nid, level_ups):
        klass = DB.classes.get(obj.klass)
        stat_base = klass.bases.get(stat_nid).value
        stat_growth = klass.growths.get(stat_nid).value
        stat_max = klass.max_stats.get(stat_nid).value

        average = int(stat_base + 0.5 + (stat_growth/100) * level_ups)

        # average = quantile(.5, level_ups, stat_growth/100) + stat_base
        quantile10 = Binomial.quantile(.1, level_ups, stat_growth/100) + stat_base
        quantile90 = Binomial.quantile(.9, level_ups, stat_growth/100) + stat_base
        return stat_max, average, quantile10, quantile90

class UnitStatAveragesModel(ClassStatAveragesModel):
    def __init__(self, columns, current, parent=None):
        VirtualListModel.__init__(self, parent)
        self.window = parent
        self._columns = self._headers = columns
        self.current = current
        self.get_rows()

    def get_rows(self):
        klass = DB.classes.get(self.current.klass)  
        max_level = klass.max_level
        self._rows = []
        for i in [1] + list(range(5, max_level, 5)) + [max_level]:
            self._rows.append((klass.nid, i, i))
        true_levels = 0
        while klass.turns_into:
            true_levels += max_level
            klass = DB.classes.get(klass.turns_into[0])  
            if klass:
                max_level = klass.max_level
                for i in [1] + list(range(5, max_level, 5)) + [max_level]:
                    self._rows.append((klass.nid, i, i + true_levels))
            else:
                return

    def set_current(self, current):
        self.current = current
        self.get_rows()
        self.layoutChanged.emit()

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            nid, level, true_level = self._rows[idx]
            # print(nid, level, true_level, flush=True)
            long_name = DB.classes.get(nid).name
            row = long_name + " " + str(level)
            # print(row)
            return row
        elif orientation == Qt.Horizontal:
            return self._columns[idx]

    def determine_average(self, obj, stat_nid, level_ups):
        stat_base = obj.bases.get(stat_nid).value
        stat_growth = obj.growths.get(stat_nid).value
        average = 0.5
        quantile10 = 0
        quantile90 = 0
        classes = [obj.klass]
        base_klass = DB.classes.get(obj.klass)
        tier = base_klass.tier
        turns_into = [k for k in base_klass.turns_into if DB.classes.get(k).tier == tier + 1]
        if level_ups > base_klass.max_level - 1 and turns_into:
            classes.append(turns_into[0])
            level_ups -= 1  # In order to promote
        for idx, klass in enumerate(classes):
            klass = DB.classes.get(klass)
            if idx == 0:
                ticks = min(level_ups, klass.max_level - obj.level)
            else:
                ticks = min(level_ups, klass.max_level - 1)
            level_ups -= ticks
            growth_bonus = klass.growth_bonus.get(stat_nid).value        
            stat_max = klass.max_stats.get(stat_nid).value
            if idx > 0:
                promotion_bonus = klass.promotion.get(stat_nid).value
            else:
                promotion_bonus = stat_base
            growth = (stat_growth + growth_bonus)/100
            average += min(stat_max, promotion_bonus + (growth * ticks))
            quantile10 += min(stat_max, Binomial.quantile(.1, ticks, growth) + promotion_bonus)
            quantile90 += min(stat_max, Binomial.quantile(.9, ticks, growth) + promotion_bonus)
        return stat_max, int(average), quantile10, quantile90

    def get_data(self, index):
        base_level = self.current.level
        nid, level, true_level = self._rows[index.row()]
        stat_nid = self._columns[index.column()]
        vals = self.determine_average(self.current, stat_nid, max(0, true_level - base_level))
        avg = vals[self.average_idx]
        maxim = vals[0]
        return maxim, avg
