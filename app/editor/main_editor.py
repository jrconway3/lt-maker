from PyQt5.QtWidgets import QMainWindow, QUndoStack, QAction, QMenu, QMessageBox, QDockWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from app.editor.map_view import MapView
from app.editor.level_menu import LevelMenu

class MainEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Lex Talionis Game Maker -- rainlash')

        self.map_view = MapView(self)
        self.setCentralWidget(self.map_view)

        self.undo_stack = QUndoStack(self)

        self.create_actions()
        self.create_menus()
        self.create_toolbar()

        self.create_level_dock()

        self.map_view.update_view()

    # === Create Menu ===
    def create_actions(self):
        self.save_as_name = None

        self.new_act = QAction(QIcon('icons/file-plus.png'), "&New Project...", self, shortcut="Ctrl+N", triggered=self.new)
        self.open_act = QAction(QIcon('icons/folder.png'), "&Open Project...", self, shortcut="Ctrl+O", triggered=self.open)
        self.save_act = QAction(QIcon('icons/save.png'), "&Save Project", self, shortcut="Ctrl+S", triggered=self.save)
        self.save_as_act = QAction(QIcon('icons/save.png'), "Save Project As...", self, shortcut="Ctrl+Shift+S", triggered=self.save_as)
        # self.export_act = QAction("&Export...", self, shortcut="Ctrl+E", triggered=self.export)
        # self.export_as_act = QAction("Export to...", self, shortcut="Ctrl+Shift+E", triggered=self.export_as)
        self.quit_act = QAction(QIcon('icons/x.png'), "&Quit", self, shortcut="Ctrl+Q", triggered=self.close)

        self.undo_act = QAction(QIcon('icons/corner-up-left.png'), "Undo", self, shortcut="Ctrl+Z", triggered=self.undo)
        self.redo_act = QAction(QIcon('icons/corner-up-right.png'), "Redo", self, triggered=self.redo)
        self.redo_act.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])

        self.about_act = QAction("&About", self, triggered=self.about)

    def create_menus(self):
        file_menu = QMenu("File", self)
        file_menu.addAction(self.new_act)
        file_menu.addAction(self.open_act)
        file_menu.addSeparator()
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.save_as_act)
        # file_menu.addAction(self.export_act)
        # file_menu.addAction(self.export_as_act)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_act)

        edit_menu = QMenu("Edit", self)
        edit_menu.addAction(self.undo_act)
        edit_menu.addAction(self.redo_act)

        help_menu = QMenu("Help", self)
        help_menu.addAction(self.about_act)

        self.menuBar().addMenu(file_menu)
        self.menuBar().addMenu(edit_menu)
        self.menuBar().addMenu(help_menu)

    def create_toolbar(self):
        pass

    def create_level_dock(self):
        self.level_dock = QDockWidget("Levels", self)
        self.level_menu = LevelMenu(self)
        self.level_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.level_dock.setWidget(self.level_menu)
        self.level_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.level_dock)

    def new(self):
        pass

    def open(self):
        pass

    def save(self, new=False):
        pass

    def save_as(self):
        self.save(True)

    def maybe_save(self):
        if not self.undo_stack.isClean():
            ret = QMessageBox.warning(self, "Map Editor", "The current map may have been modified.\n"
                                            "Do you want to save your changes?",
                                            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def undo(self):
        self.undo_stack.undo()
        self.map_view.update_view()

    def redo(self):
        self.undo_stack.redo()
        self.map_view.update_view()

    def about(self):
        QMessageBox.about(self, "About Lex Talionis Game Maker",
            "<p>This is the <b>Lex Talionis</b> Game Maker.</p>"
            "<p>Check out https://gitlab.com/rainlash/lex-talionis/wikis/home "
            "for more information and helpful tutorials.</p>"
            "<p>This program has been freely distributed under the MIT License.</p>"
            "<p>Copyright 2014-2019 rainlash.</p>")