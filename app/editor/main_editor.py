import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

from PyQt5.QtWidgets import QMainWindow, QUndoStack, QAction, QMenu, QMessageBox, \
    QDockWidget, QFileDialog, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDir, QSettings

from app.data.database import DB

from app.editor.map_view import MapView
from app.editor.level_menu import LevelMenu
from app.editor.database_editor import DatabaseEditor

class PropertiesMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

class TerrainPainterMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

class EventTileMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

class UnitsMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

class ReinforcementGroupsMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

class Dock(QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.main_editor = parent
        self.visibilityChanged.connect(self.visible)

    def visible(self, visible):
        title = str(self.windowTitle())
        self.main_editor.dock_visibility[title] = visible
        if visible:
            message = None
            if message:
                self.main_editor.status_bar.showMessage(message)
        self.main_editor.update_view()

class MainEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Lex Talionis Game Maker -- rainlash')
        self.settings = QSettings("rainlash", "Lex Talionis")
        self.settings.setDefaultFormat(QSettings.IniFormat)

        self.map_view = MapView(self)
        self.setCentralWidget(self.map_view)

        self.undo_stack = QUndoStack(self)

        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        self.create_statusbar()

        self.create_level_dock()
        self.create_edit_dock()

        self.map_view.update_view()

    def set_current_level(self, level):
        self.map_view.set_current_map(level.tilemap)

    def update_view(self):
        self.map_view.update_view()

    # === Create Menu ===
    def create_actions(self):
        self.current_save_loc = None

        self.new_act = QAction(QIcon('icons/file-plus.png'), "&New Project...", self, shortcut="Ctrl+N", triggered=self.new)
        self.open_act = QAction(QIcon('icons/folder.png'), "&Open Project...", self, shortcut="Ctrl+O", triggered=self.open)
        self.save_act = QAction(QIcon('icons/save.png'), "&Save Project", self, shortcut="Ctrl+S", triggered=self.save)
        self.save_as_act = QAction(QIcon('icons/save.png'), "Save Project As...", self, shortcut="Ctrl+Shift+S", triggered=self.save_as)
        self.quit_act = QAction(QIcon('icons/x.png'), "&Quit", self, shortcut="Ctrl+Q", triggered=self.close)

        self.undo_act = QAction(QIcon('icons/corner-up-left.png'), "Undo", self, shortcut="Ctrl+Z", triggered=self.undo)
        self.redo_act = QAction(QIcon('icons/corner-up-right.png'), "Redo", self, triggered=self.redo)
        self.redo_act.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])

        self.about_act = QAction("&About", self, triggered=self.about)

        # Toolbar actions
        self.modify_tilemap_act = QAction(QIcon('icons/map.png'), "Edit Map", self, triggered=self.edit_map)
        self.back_to_main_act = QAction(QIcon('icons/back.png'), "Back", self, triggered=self.edit_global)
        self.modify_database_act = QAction(QIcon('icons/database.png'), "Edit Database", self, triggered=self.edit_database)
        self.modify_events_act = QAction(QIcon('icons/event.png'), "Edit Events", self, triggered=self.edit_events)
        self.test_play_act = QAction(QIcon('icons/play.png'), "Test Play", self, triggered=self.test_play)

    def create_menus(self):
        file_menu = QMenu("File", self)
        file_menu.addAction(self.new_act)
        file_menu.addAction(self.open_act)
        file_menu.addSeparator()
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.save_as_act)
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
        self.toolbar = self.addToolBar("Edit")
        self.toolbar.addAction(self.modify_tilemap_act)
        self.toolbar.addAction(self.modify_database_act)
        self.toolbar.addAction(self.modify_events_act)
        self.toolbar.addAction(self.test_play_act)

    def create_statusbar(self):
        self.status_bar = self.statusBar()

    def create_level_dock(self):
        self.level_dock = QDockWidget("Levels", self)
        self.level_menu = LevelMenu(self)
        self.level_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.level_dock.setWidget(self.level_menu)
        self.level_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.level_dock)

    def create_edit_dock(self):
        self.docks = {}

        self.docks['Properties'] = Dock("Properties", self)
        self.properties_menu = PropertiesMenu(self)
        self.docks['Properties'].setWidget(self.properties_menu)

        self.docks['Terrain'] = Dock("Terrain", self)
        self.terrain_painter_menu = TerrainPainterMenu(self)
        self.docks['Terrain'].setWidget(self.terrain_painter_menu)

        # self.docks['Triggers'] = Dock("Triggers", self)
        # self.trigger_region_menu = TriggerRegionMenu(self)
        # self.docks['Triggers'].setWidget(self.trigger_region_menu)

        self.docks['Event Tiles'] = Dock("Event Tiles", self)
        self.event_tile_menu = EventTileMenu(self)
        self.docks['Event Tiles'].setWidget(self.event_tile_menu)

        self.docks['Units'] = Dock("Units", self)
        self.units_menu = UnitsMenu(self)
        self.docks['Units'].setWidget(self.units_menu)

        self.docks['Reinforcements'] = Dock("Reinforcements", self)
        self.reinforcement_groups_menu = ReinforcementGroupsMenu(self)
        self.docks['Reinforcements'].setWidget(self.reinforcement_groups_menu)

        for title, dock in self.docks.items():
            dock.setAllowedAreas(Qt.RightDockWidgetArea)
            dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Tabify dock widgets
        self.tabifyDockWidget(self.docks['Properties'], self.docks['Terrain'])
        self.tabifyDockWidget(self.docks['Terrain'], self.docks['Event Tiles'])
        self.tabifyDockWidget(self.docks['Event Tiles'], self.docks['Units'])
        self.tabifyDockWidget(self.docks['Units'], self.docks['Reinforcements'])
        self.docks['Properties'].raise_()

        for title, dock in self.docks.items():
            dock.setEnabled(False)

        self.dock_visibility = {k: False for k in self.docks.keys()}

    def new(self):
        if self.maybe_save():
            DB.init_load()
            self.update_view()

    def open(self):
        if self.maybe_save():
            starting_path = self.current_save_loc or QDir.currentPath()
            fn, ok = QFileDialog.getOpenFileName(self, "Open Project", starting_path,
                                                 "LT Project Files (*.ltproj);;All Files (*)")
            if ok:
                self.current_save_loc = fn
                self.load()
            else:
                return False

    def auto_open(self):
        path = self.settings.value("starting_path", None)

        if path and os.path.exists(path):
            self.current_save_loc = path
            self.load()

    def load(self):
        if os.path.exists(self.current_save_loc):
            with open(self.current_save_loc, 'rb') as load_fp:
                data = pickle.load(load_fp)

            DB.restore(data)

            self.status_bar.showMessage("Loaded project from %s" % self.current_save_loc)
            self.update_view()

    def save(self, new=False):
        if new or not self.current_save_loc:
            starting_path = self.current_save_loc or QDir.currentPath()
            fn, ok = QFileDialog.getSaveFileName(self, "Save Project", starting_path, 
                                                 "LT Project Files (*.ltproj);;All Files (*)")
            if ok:
                self.current_save_loc = fn
            else:
                return False
            new = True

        if new:
            if os.path.exists(self.current_save_loc):
                ret = QMessageBox.warning(self, "Save Project", "The file already exists.\nDo you want to overwrite it?", 
                                          QMessageBox.Save | QMessageBox.Cancel)
                if ret == QMessageBox.Save:
                    pass
                else:
                    return False

        # Actually gather information needed to save
        project = DB.save()

        with open(self.current_save_loc, 'wb') as save_fp:
            # Remove the -1 here if you want to interrogate the pickled save
            pickle.dump(project, save_fp, -1)

        self.status_bar.showMessage('Saved project to %s' % self.current_save_loc)

    def save_as(self):
        self.save(True)

    def maybe_save(self):
        if not self.undo_stack.isClean():
            ret = QMessageBox.warning(self, "Main Editor", "The current map may have been modified.\n"
                                            "Do you want to save your changes?",
                                            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            self.settings.setValue("starting_path", self.current_save_loc)
            event.accept()
        else:
            event.ignore()

    def undo(self):
        self.undo_stack.undo()
        self.update_view()

    def redo(self):
        self.undo_stack.redo()
        self.update_view()

    def edit_map(self):
        self.toolbar.insertAction(self.modify_tilemap_act, self.back_to_main_act)
        self.toolbar.removeAction(self.modify_tilemap_act)
        
        for title, dock in self.docks.items():
            dock.setEnabled(True)
        # self.removeDockWidget(self.level_dock)
        self.level_dock.setEnabled(False)

    def edit_global(self):
        self.toolbar.insertAction(self.back_to_main_act, self.modify_tilemap_act)
        self.toolbar.removeAction(self.back_to_main_act)

        for title, dock in self.docks.items():
            dock.setEnabled(False)
        self.level_dock.setEnabled(True)

    def edit_database(self):
        dialog = DatabaseEditor(self)
        dialog.exec_()

    def edit_events(self):
        pass

    def test_play(self):
        pass

    def about(self):
        QMessageBox.about(self, "About Lex Talionis Game Maker",
            "<p>This is the <b>Lex Talionis</b> Game Maker.</p>"
            "<p>Check out https://gitlab.com/rainlash/lex-talionis/wikis/home "
            "for more information and helpful tutorials.</p>"
            "<p>This program has been freely distributed under the MIT License.</p>"
            "<p>Copyright 2014-2019 rainlash.</p>")
