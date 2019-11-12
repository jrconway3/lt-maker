from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QTreeView
from PyQt5.QtCore import Qt

from app.editor.custom_gui import MultiAttrListModel, RightClickTreeView

class BasicListWidget(QWidget):
    def __init__(self, data, title, attrs, dlgate, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current = data

        self.model = MultiAttrListModel(self.current, attrs, None, self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        delegate = dlgate(self.view)
        self.view.setItemDelegate(delegate)
        for col in range(len(attrs)):
            self.view.resizeColumnToContents(col)

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, 1, 0, 1, 2)
        self.setLayout(layout)

        label = QLabel(title)
        label.setAlignment(Qt.AlignBottom)
        layout.addWidget(label, 0, 0)

        self._actions = []

    def set_current(self, data):
        self.current = data
        self.model.set_new_data(self.current)

class AppendListWidget(QWidget):
    def __init__(self, data, title, attrs, dlgate, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current = data

        self.model = MultiAttrListModel(self.current, attrs, None, self)
        self.view = RightClickTreeView(self)
        self.view.setModel(self.model)
        delegate = dlgate(self.view)
        self.view.setItemDelegate(delegate)
        for col in range(len(attrs)):
            self.view.resizeColumnToContents(col)

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view, 1, 0, 1, 2)
        self.setLayout(layout)

        label = QLabel(title)
        label.setAlignment(Qt.AlignBottom)
        layout.addWidget(label, 0, 0)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self.model.add_new_row)
        layout.addWidget(add_button, 0, 1, alignment=Qt.AlignRight)

    def set_current(self, data):
        self.current = data
        self.model.set_new_data(self.current)
