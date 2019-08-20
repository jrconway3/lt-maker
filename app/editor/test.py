from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class McostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = McostModel(self)
        self.view = QTableView()
        self.view.setModel(self.model)

        layout = QGridLayout(self)
        layout.addWidget(self.view, 0, 0, 1, 2)
        self.setLayout(layout)

        column_header_view = ColumnHeaderView()
        custom_style = VerticalTextHeaderStyle(self.style())
        # column_header_view.setStyle(custom_style)
        self.view.setHorizontalHeader(column_header_view)

class VerticalTextHeaderStyle(QProxyStyle):
    def drawControl(self, element, option, painter, parent=None):
        if (element == QStyle.CE_HeaderLabel):
            header = option
            painter.save()
            painter.translate(header.rect.center().x() + 3, header.rect.bottom())
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

    def sizeHint(self):
        return QSize(0, self._get_text_width() + 2 * self._margin)

    def _get_text_width(self):
        return max([self._metrics.width(self._get_data(i)) for i in range(self.model().columnCount())])

    def _get_data(self, index):
        return self.model().headerData(index, self.orientation())

class McostModel(QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self.data = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        self.column_headers = ["Alpha", "Beta", "Gamma"]
        self.row_headers = ["Uno", "Dos", "Tres"]

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:  # Row
            return self.row_headers[idx]
        elif orientation == Qt.Horizontal:  # Column
            return self.column_headers[idx]
        return None

    def rowCount(self, parent=None):
        return len(self.row_headers)

    def columnCount(self, parent=None):
        return len(self.column_headers)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.data[index.column()][index.row()]
        return None

# Testing
# Run "python -m app.editor.mcost_dialog" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = McostDialog()
    window.show()
    app.exec_()
