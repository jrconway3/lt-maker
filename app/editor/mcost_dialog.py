from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTableView, QInputDialog
from PyQt5.QtWidgets import QGridLayout, QPushButton, QLineEdit, QItemDelegate
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import Qt

from app.data.database import DB

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

        self.view.horizontalHeader().sectionDoubleClicked.connect(self.model.change_horiz_header)
        self.view.verticalHeader().sectionDoubleClicked.connect(self.model.change_vert_header)

        layout = QGridLayout(self)
        layout.addWidget(self.view, 0, 0, 1, 2)
        self.setLayout(layout)

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

class McostDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QIntValidator(1, 99))
        return editor

class McostModel(QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self.data = DB.mcost
        self.rows = list(self.data.keys())

    def add_terrain_type(self):
        self.data['New'] = [1]*len(list(self.data.values())[0])
        self.rows = list(self.data.keys())
        self.layoutChanged.emit()

    def add_movement_type(self):
        self.data.column_headers.append('New')
        for k in self.data.keys():
            self.data[k].append(1)
        self.layoutChanged.emit()

    def headerData(self, idx, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:  # Row
            return self.rows[idx]
        elif orientation == Qt.Horizontal:  # Column
            return self.data.column_headers[idx]
        return None

    def change_horiz_header(self, idx):
        old_header = self.data.column_headers[idx]
        new_header, ok = QInputDialog.getText(self.parent(), 'Change Movement Type', 'Header:', QLineEdit.Normal, old_header)
        if ok:
            self.data.column_headers[idx] = new_header

    def change_vert_header(self, idx):
        old_header = self.rows[idx]
        new_header, ok = QInputDialog.getText(self.parent(), 'Change Terrain Type', 'Header:', QLineEdit.Normal, old_header)
        if ok:
            self.data[new_header] = self.data[old_header]
            del self.data[old_header]
            self.rows = list(self.data.keys())

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data['Normal'])

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.data[self.rows[index.row()]][index.column()]
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        self.data[self.rows[index.row()]][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    # Determines how each item behaves
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

# Testing
# Run "python -m app.editor.mcost_dialog" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = McostDialog()
    window.show()
    app.exec_()
