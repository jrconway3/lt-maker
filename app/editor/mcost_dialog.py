from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTableView, QInputDialog, QHeaderView
from PyQt5.QtWidgets import QGridLayout, QPushButton, QLineEdit, QItemDelegate
from PyQt5.QtGui import QIntValidator, QFontMetrics
from PyQt5.QtWidgets import QStyle, QProxyStyle
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import Qt, QSize

from app.data.database import DB
import app.utilities as utilities

class McostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Terrain Movement Cost')
        self.setMinimumSize(640, 480)

        self.model = McostModel(self)
        self.view = QTableView()
        self.view.setModel(self.model)
        delegate = McostDelegate(self.view)
        self.view.setItemDelegate(delegate)

        layout = QGridLayout(self)
        layout.addWidget(self.view, 0, 0, 1, 2)
        self.setLayout(layout)

        column_header_view = ColumnHeaderView()
        self.view.setHorizontalHeader(column_header_view)

        self.view.horizontalHeader().sectionDoubleClicked.connect(self.model.change_horiz_header)
        self.view.verticalHeader().sectionDoubleClicked.connect(self.model.change_vert_header)

        self.view.resizeColumnsToContents()

        new_terrain_button = QPushButton("Add Terrain Type")
        new_terrain_button.clicked.connect(self.model.add_terrain_type)
        new_mtype_button = QPushButton("Add Movement Type")
        new_mtype_button.clicked.connect(self.model.add_movement_type)
        self.buttonbox = QDialogButtonBox(Qt.Horizontal, self)
        self.buttonbox.addButton(new_terrain_button, QDialogButtonBox.ActionRole)
        self.buttonbox.addButton(new_mtype_button, QDialogButtonBox.ActionRole)
        layout.addWidget(self.buttonbox, 1, 0, alignment=Qt.AlignLeft)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        layout.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

class VerticalTextHeaderStyle(QProxyStyle):
    def __init__(self, fontHeight):
        super().__init__()
        self.half_font_height = fontHeight / 2

    def drawControl(self, element, option, painter, parent=None):
        if (element == QStyle.CE_HeaderLabel):
            header = option
            painter.save()
            painter.translate(header.rect.center().x() + self.half_font_height, header.rect.bottom())
            painter.rotate(-90)
            painter.drawText(0, 0, header.text)
            painter.restore()
        else:
            super().drawControl(element, option, painter, parent)

class ColumnHeaderView(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._metrics = QFontMetrics(self.font())
        self._descent = self._metrics.descent()
        self._margin = 10
        custom_style = VerticalTextHeaderStyle(self.font().pixelSize() + 1)
        self.setStyle(custom_style)

    def sizeHint(self):
        return QSize(0, self._get_text_width() + 2 * self._margin)

    def _get_text_width(self):
        return max([self._metrics.width(self._get_data(i)) for i in range(self.model().columnCount())])

    def _get_data(self, index):
        return self.model().headerData(index, self.orientation())

class McostDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QIntValidator(1, 99))
        return editor

class McostModel(QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._data = DB.mcost

    def add_terrain_type(self):
        new_row_name = utilities.get_next_name('New', self._data.row_headers)
        self._data.add_row(new_row_name)
        self.layoutChanged.emit()

    def add_movement_type(self):
        new_col_name = utilities.get_next_name('New', self._data.column_headers)
        self._data.add_column(new_col_name)
        self.layoutChanged.emit()

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:  # Row
            return self._data.row_headers[idx]
        elif orientation == Qt.Horizontal:  # Column
            return self._data.column_headers[idx]
        return None

    def change_horiz_header(self, idx):
        old_header = self._data.column_headers[idx]
        new_header, ok = QInputDialog.getText(self.parent(), 'Change Movement Type', 'Header:', QLineEdit.Normal, old_header)
        if ok:
            self._data.column_headers[idx] = utilities.get_next_name(new_header, self._data.column_headers)

    def change_vert_header(self, idx):
        old_header = self._data.row_headers[idx]
        new_header, ok = QInputDialog.getText(self.parent(), 'Change Terrain Type', 'Header:', QLineEdit.Normal, old_header)
        if ok:
            self._data.row_headers[idx] = utilities.get_next_name(new_header, self._data.row_headers)

    def rowCount(self, parent=None):
        return self._data.height()

    def columnCount(self, parent=None):
        return self._data.width()

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._data.get((index.column(), index.row()))
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        self._data.set((index.column(), index.row()), value)
        self.dataChanged.emit(index, index)
        return True

    # Determines how each item behaves
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren

# Testing
# Run "python -m app.editor.mcost_dialog" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = McostDialog()
    window.show()
    app.exec_()
