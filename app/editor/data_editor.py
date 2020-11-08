from PyQt5.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QTabWidget, \
    QSizePolicy
from PyQt5.QtCore import Qt, QSettings

from app.resources.resources import RESOURCES
from app.data.database import DB

class SingleDatabaseEditor(QDialog):
    def __init__(self, tab, parent=None):
        super().__init__(parent)
        self.window = parent
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.save()

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        self.tab = tab.create(self)
        self.grid.addWidget(self.tab, 0, 0, 1, 2)

        self.setWindowTitle(self.tab.windowTitle())

        # Restore Geometry
        settings = QSettings("rainlash", "Lex Talionis")
        geometry = settings.value(self._type() + " geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value(self._type() + " state")
        if state:
            self.tab.splitter.restoreState(state)

    def accept(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        self.save_geometry()
        # if current_proj:
        #     DB.serialize(current_proj)
        super().accept()

    def reject(self):
        self.restore()
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        self.save_geometry()
        # if current_proj:
        #     DB.serialize(current_proj)
        super().reject()

    def save(self):
        self.saved_data = DB.save()
        return self.saved_data

    def restore(self):
        DB.restore(self.saved_data)
        
    def apply(self):
        self.save()

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def _type(self):
        return self.tab.__class__.__name__

    def save_geometry(self):
        settings = QSettings("rainlash", "Lex Talionis")
        settings.setValue(self._type() + " geometry", self.saveGeometry())
        settings.setValue(self._type() + " state", self.tab.splitter.saveState())
        print(self._type(), "Save Geometry")

class SingleResourceEditor(QDialog):
    def __init__(self, tab, resource_types=None, parent=None):
        super().__init__(parent)
        self.window = parent
        self.resource_types = resource_types
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.tab = tab.create(self)
        self.grid.addWidget(self.tab, 0, 0, 1, 2)

        self.setWindowTitle(self.tab.windowTitle())

    def accept(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        if current_proj:
            RESOURCES.save(current_proj, self.resource_types)
        super().accept()

    def reject(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        if current_proj:
            RESOURCES.reload(current_proj)
        super().reject()

class MultiResourceEditor(QDialog):
    def __init__(self, tabs, resource_types, parent=None):
        super().__init__(parent)
        self.window = parent
        self.resource_types = resource_types
        self.setWindowTitle("Resource Editor")
        self.setStyleSheet("font: 10pt;")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.grid = QGridLayout(self)
        self.setLayout(self.grid)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.grid.addWidget(self.buttonbox, 1, 1)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.tab_bar = QTabWidget(self)
        self.grid.addWidget(self.tab_bar, 0, 0, 1, 2)
        self.tabs = []
        for tab in tabs:
            new_tab = tab.create(self)
            self.tabs.append(new_tab)
            self.tab_bar.addTab(new_tab, new_tab.windowTitle())

        self.current_tab = self.tab_bar.currentWidget()
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        # Make each tab individually resizable
        for i in range(self.tab_bar.count()):
            if i == idx:
                self.tab_bar.widget(i).setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                self.tab_bar.widget(i).setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        new_tab = self.tab_bar.currentWidget()
        self.current_tab = new_tab
        self.current_tab.update_list()
        self.current_tab.reset()

    def accept(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        if current_proj:
            RESOURCES.save(current_proj, self.resource_types)
        super().accept()

    def reject(self):
        settings = QSettings("rainlash", "Lex Talionis")
        current_proj = settings.value("current_proj", None)
        if current_proj:
            RESOURCES.reload(current_proj)
        super().reject()
