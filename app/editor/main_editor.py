import os

from PyQt5.QtWidgets import QMainWindow, QUndoStack, QAction, QMenu, QMessageBox, \
    QDockWidget, QFileDialog, QWidget, QLabel, QFrame, QDesktopWidget, \
    QToolButton, QWidgetAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDir, QSettings

from app.data.constants import VERSION
from app.data.resources import RESOURCES
from app.data.database import DB

from app.editor.timer import TIMER

from app.editor.preferences import PreferencesDialog
from app.editor.map_view import MapView
from app.editor.level_menu import LevelDatabase
from app.editor.database_editor import DatabaseEditor
from app.editor.resource_editor import ResourceEditor
from app.editor.property_menu import PropertiesMenu
from app.editor.unit_painter_menu import UnitPainterMenu
from app.editor.translation_widget import TranslationDialog

__version__ = VERSION

class EventTileMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def on_visibility_changed(self, state):
        pass

class ReinforcementGroupsMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def on_visibility_changed(self, state):
        pass

class Dock(QDockWidget):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.main_editor = parent
        self.visibilityChanged.connect(self.on_visible)

    def on_visible(self, visible):
        title = str(self.windowTitle())
        self.main_editor.dock_visibility[title] = visible
        self.main_editor.docks[title].widget().on_visibility_changed(visible)
        if visible:
            message = None
            if message:
                self.main_editor.status_bar.showMessage(message)
        self.main_editor.update_view()

class MainEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_title = 'LT Maker'
        self.setWindowTitle(self.window_title)
        self.settings = QSettings("rainlash", "Lex Talionis")
        self.settings.setDefaultFormat(QSettings.IniFormat)
        # Will be overwritten by auto-open
        desktop = QDesktopWidget()
        main_screen_size = desktop.availableGeometry(desktop.primaryScreen())

        # Use setFixedSize to make it permanent and unchangeable
        self.default_size = main_screen_size.width()*0.7, main_screen_size.height()*0.7
        self.resize(*self.default_size)

        self.map_view = MapView(self)
        self.setCentralWidget(self.map_view)

        self.undo_stack = QUndoStack(self)
        self.undo_stack.cleanChanged.connect(self.on_clean_changed)

        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        self.create_statusbar()

        self.current_level = None

        self.global_mode = True
        self.create_level_dock()
        self.create_edit_dock()

        # Actually load data
        # DB.deserialize()
        # DB.init_load()

        self.auto_open()
        
        if len(DB.levels) == 0:
            self.level_menu.create_initial_level()

        self.map_view.update_view()

        TIMER.tick_elapsed.connect(self.map_view.update_view)

    def on_clean_changed(self, clean):
        # Change Title
        if clean:
            pass
        else:
            if not self.window_title.startswith('*'):
                self.window_title = '*' + self.window_title

    def set_window_title(self, title):
        if self.window_title.startswith('*'):
            self.window_title = '*' + title + ' -- LT Maker %s' % (__version__)
        else:
            self.window_title = title + ' -- LT Maker %s' % (__version__)
        self.setWindowTitle(self.window_title)

    def get_current_level(self):
        return self.current_level

    def set_current_level(self, level):
        self.current_level = level
        self.test_current_act.setEnabled(True)
        self.set_current_tilemap(level.tilemap)
        self.unit_painter_menu.set_current_level(level)
        self.update_view()

    def set_current_tilemap(self, tilemap_nid):
        tilemap = RESOURCES.tilemaps.get(tilemap_nid)
        self.map_view.set_current_map(tilemap)

    def current_level_index(self):
        return DB.levels.index(self.current_level)

    def update_view(self):
        self.level_menu.update_view()
        self.map_view.update_view()

    # === Create Menu ===
    def create_actions(self):
        self.current_proj = None

        self.new_act = QAction(QIcon('icons/file-plus.png'), "&New Project...", self, shortcut="Ctrl+N", triggered=self.new)
        self.open_act = QAction(QIcon('icons/folder.png'), "&Open Project...", self, shortcut="Ctrl+O", triggered=self.open)
        self.save_act = QAction(QIcon('icons/save.png'), "&Save Project", self, shortcut="Ctrl+S", triggered=self.save)
        self.save_as_act = QAction(QIcon('icons/save.png'), "Save Project As...", self, shortcut="Ctrl+Shift+S", triggered=self.save_as)
        # self.build_act = QAction(QIcon(), "Build Project...", self, shortcut="Ctrl+B", triggered=self.build_project)
        self.quit_act = QAction(QIcon('icons/x.png'), "&Quit", self, shortcut="Ctrl+Q", triggered=self.close)

        self.undo_act = QAction(QIcon('icons/corner-up-left.png'), "Undo", self, shortcut="Ctrl+Z", triggered=self.undo)
        self.redo_act = QAction(QIcon('icons/corner-up-right.png'), "Redo", self, triggered=self.redo)
        self.redo_act.setShortcuts(["Ctrl+Y", "Ctrl+Shift+Z"])

        self.zoom_in_act = QAction(QIcon('icons/zoom_in.png'), "Zoom in", self, shortcut="Ctrl++", triggered=self.map_view.zoom_in)
        self.zoom_out_act = QAction(QIcon('icons/zoom_out.png'), "Zoom out", self, shortcut="Ctrl+-", triggered=self.map_view.zoom_out)

        self.preferences_act = QAction("&Preferences...", self, triggered=self.edit_preferences)
        self.about_act = QAction("&About", self, triggered=self.about)

        # Test actions
        self.test_current_act = QAction(QIcon('icons/play.png'), "Test Current Chapter...", self, shortcut="F5", triggered=self.test_play_current)
        self.test_current_act.setEnabled(False)
        self.test_full_act = QAction(QIcon('icons/play_all.png'), "Test Full Game...", self, shortcut="Ctrl+F5", triggered=self.test_play)
        # self.balance_act = QAction("Preload Units...", self, triggered=self.edit_preload_units)

        # Toolbar actions
        self.modify_level_act = QAction(QIcon('icons/map.png'), "Edit Level", self, shortcut="E", triggered=self.edit_level)
        self.back_to_main_act = QAction(QIcon('icons/left_arrow.png'), "Back", self, shortcut="E", triggered=self.edit_global)
        self.modify_database_act = QAction(QIcon('icons/database.png'), "Edit Database", self, shortcut="D", triggered=self.edit_database)
        self.modify_events_act = QAction(QIcon('icons/event.png'), "Edit Events", self, shortcut="S", triggered=self.edit_events)
        self.modify_resources_act = QAction("Edit Resources...", self, shortcut="Ctrl+R", triggered=self.edit_resources)
        self.modify_translations_act = QAction("Edit Translations...", self, triggered=self.edit_translations)

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
        # Current removing undo and redo capabilities
        # edit_menu.addAction(self.undo_act)
        # edit_menu.addAction(self.redo_act)
        edit_menu.addAction(self.modify_resources_act)
        edit_menu.addAction(self.modify_translations_act)
        edit_menu.addSeparator()
        edit_menu.addAction(self.zoom_in_act)
        edit_menu.addAction(self.zoom_out_act)

        test_menu = QMenu("Test", self)
        test_menu.addAction(self.test_current_act)
        test_menu.addAction(self.test_full_act)

        help_menu = QMenu("Help", self)
        help_menu.addAction(self.about_act)
        help_menu.addAction(self.preferences_act)

        self.menuBar().addMenu(file_menu)
        self.menuBar().addMenu(edit_menu)
        self.menuBar().addMenu(test_menu)
        self.menuBar().addMenu(help_menu)

    def create_toolbar(self):
        self.toolbar = self.addToolBar("Edit")
        self.toolbar.addAction(self.modify_level_act)
        self.toolbar.addAction(self.modify_database_act)
        self.toolbar.addAction(self.modify_events_act)

        self.test_button = QToolButton(self)
        self.test_button.setIcon(QIcon('icons/play.png'))
        self.test_button.setPopupMode(QToolButton.InstantPopup)
        test_menu = QMenu("Test", self)
        test_menu.addAction(self.test_current_act)
        test_menu.addAction(self.test_full_act)
        self.test_button.setMenu(test_menu)
        self.test_button_action = QWidgetAction(self)
        self.test_button_action.setDefaultWidget(self.test_button)

        # self.toolbar.addToolButton(self.test_button)
        self.toolbar.addAction(self.test_button_action)

    def create_statusbar(self):
        self.status_bar = self.statusBar()
        self.position_bar = QLabel("", self)
        self.position_bar.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.position_bar.setMinimumWidth(100)
        self.status_bar.addPermanentWidget(self.position_bar)

    def set_position_bar(self, pos):
        if pos:
            self.position_bar.setText("Position (%d, %d)" % (pos[0], pos[1]))
        else:
            self.position_bar.setText("")

    def set_terrain(self, terrain):
        if terrain:
            self.status_bar.showMessage("Terrain")
        else:
            self.status_bar.clearMessage()

    def create_level_dock(self):
        print("Create Level Dock")
        self.level_dock = QDockWidget("Levels", self)
        self.level_menu = LevelDatabase(self)
        self.level_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.level_dock.setWidget(self.level_menu)
        self.level_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.level_dock)

    def create_edit_dock(self):
        self.docks = {}

        self.docks['Properties'] = Dock("Properties", self)
        self.properties_menu = PropertiesMenu(self)
        self.docks['Properties'].setWidget(self.properties_menu)

        # self.docks['Tiles'] = Dock("Tiles", self)
        # self.tiles_menu = TileMenu(self)
        # self.docks['Tiles'].setWidget(self.tiles_menu)

        # self.docks['Terrain'] = Dock("Terrain", self)
        # self.terrain_painter_menu = TerrainPainterMenu(self)
        # self.docks['Terrain'].setWidget(self.terrain_painter_menu)

        # self.docks['Triggers'] = Dock("Triggers", self)
        # self.trigger_region_menu = TriggerRegionMenu(self)
        # self.docks['Triggers'].setWidget(self.trigger_region_menu)

        self.docks['Event Tiles'] = Dock("Event Tiles", self)
        self.event_tile_menu = EventTileMenu(self)
        self.docks['Event Tiles'].setWidget(self.event_tile_menu)

        self.docks['Units'] = Dock("Units", self)
        self.unit_painter_menu = UnitPainterMenu(self)
        self.docks['Units'].setWidget(self.unit_painter_menu)

        # self.docks['Reinforcements'] = Dock("Reinforcements", self)
        # self.reinforcement_groups_menu = ReinforcementGroupsMenu(self)
        # self.docks['Reinforcements'].setWidget(self.reinforcement_groups_menu)

        for title, dock in self.docks.items():
            dock.setAllowedAreas(Qt.RightDockWidgetArea)
            dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
            dock.hide()
            # self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Tabify dock widgets
        # for title, dock in self.docks.items():
            # dock.setEnabled(False)

        self.dock_visibility = {k: False for k in self.docks.keys()}

    def new(self):
        if self.maybe_save():
            # Return to global
            if not self.global_mode:
                self.edit_global()

            DB.deserialize()
            self.undo_stack.setClean()
            self.set_window_title('Untitled')
            self.update_view()

    def open(self):
        if self.maybe_save():
            starting_path = self.current_proj or QDir.currentPath()
            fn = QFileDialog.getExistingDirectory(self, "Open Project Directory", starting_path)
            if fn:
                self.current_proj = fn
                self.load()
            else:
                return False

    def auto_open(self):
        path = self.settings.value("current_proj", None)
        print("Auto Open: %s" % path)

        if path and os.path.exists(path):
            self.current_proj = path
            self.load()
            return True
        else:
            return False

    def load(self):
        if os.path.exists(self.current_proj):
            if not self.global_mode:
                self.edit_global()

            title = os.path.split(self.current_proj)[-1]
            self.set_window_title(title)

            RESOURCES.load(self.current_proj)
            DB.deserialize(self.current_proj)
            # DB.init_load()

            self.undo_stack.clear()
            print("Loaded project from %s" % self.current_proj)
            self.status_bar.showMessage("Loaded project from %s" % self.current_proj)
            self.update_view()

    def save(self, new=False):
        if new or not self.current_proj:
            starting_path = self.current_proj or QDir.currentPath()
            fn, ok = QFileDialog.getSaveFileName(self, "Save Project", starting_path, 
                                                 "All Files (*)")
            if ok:
                if fn.endswith('.ltproj'):
                    self.current_proj = fn
                else:
                    self.current_proj = fn + '.ltproj'
            else:
                return False
            new = True

        if new:
            if os.path.exists(self.current_proj):
                ret = QMessageBox.warning(self, "Save Project", "The file already exists.\nDo you want to overwrite it?", 
                                          QMessageBox.Save | QMessageBox.Cancel)
                if ret == QMessageBox.Save:
                    pass
                else:
                    return False

        # Set title
        # title = os.path.split(self.current_save_loc)[-1].split('.')[0]
        title = os.path.split(self.current_proj)[-1]
        self.set_window_title(title)
        # Remove asterisk on window title
        if self.window_title.startswith('*'):
            self.window_title = self.window_title[1:]

        # Make directory for saving if it doesn't already exist
        if not os.path.isdir(self.current_proj):
            os.mkdir(self.current_proj)

        # Actually save project
        RESOURCES.serialize(self.current_proj)
        DB.serialize(self.current_proj)
        
        self.status_bar.showMessage('Saved project to %s' % self.current_proj)
        self.undo_stack.setClean()
        return True

    def save_as(self):
        self.save(True)

    def maybe_save(self):
        # if not self.undo_stack.isClean():
        if True:  # For now, since undo stack is not being used
            ret = QMessageBox.warning(self, "Main Editor", "The current project may have been modified.\n"
                                            "Do you want to save your changes?",
                                            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            print("Setting current project %s" % self.current_proj)
            self.settings.setValue("current_proj", self.current_proj)
            event.accept()
        else:
            event.ignore()

    def undo(self):
        self.status_bar.showMessage('Undo: %s' % self.undo_stack.undoText())
        self.undo_stack.undo()
        self.update_view()

    def redo(self):
        self.status_bar.showMessage('Redo: %s' % self.undo_stack.redoText())
        self.undo_stack.redo()
        self.update_view()

    def edit_level(self):
        if self.current_level:
            self.toolbar.insertAction(self.modify_level_act, self.back_to_main_act)
            self.toolbar.removeAction(self.modify_level_act)
            
            for title, dock in self.docks.items():
                self.addDockWidget(Qt.RightDockWidgetArea, dock)

            # Order is REALLY IMPORTANT. Must tabify before show.
            self.tabifyDockWidget(self.docks['Properties'], self.docks['Event Tiles'])
            # self.tabifyDockWidget(self.docks['Terrain'], self.docks['Event Tiles'])
            self.tabifyDockWidget(self.docks['Event Tiles'], self.docks['Units'])
            # self.tabifyDockWidget(self.docks['Units'], self.docks['Reinforcements'])

            for title, dock in self.docks.items():
                dock.show()
            
            self.docks['Properties'].raise_()

            self.level_dock.hide()
            self.removeDockWidget(self.level_dock)

            self.global_mode = False

    def edit_global(self):
        self.toolbar.insertAction(self.back_to_main_act, self.modify_level_act)
        self.toolbar.removeAction(self.back_to_main_act)

        for title, dock in self.docks.items():
            dock.hide()
            self.removeDockWidget(dock)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.level_dock)        
        self.level_dock.show()

        self.global_mode = True

    def edit_database(self):
        dialog = DatabaseEditor(self)
        dialog.exec_()

    def edit_resources(self):
        dialog = ResourceEditor(self)
        dialog.exec_()

    def edit_translations(self):
        DB.deserialize()
        dialog = TranslationDialog.create()
        dialog.exec_()
        DB.serialize()

    def edit_events(self):
        pass

    def test_play(self):
        from app.engine import driver, game_state
        title = DB.constants.get('title').value
        driver.start(title, from_editor=True)
        game = game_state.start_game()
        driver.run(game)

    def test_play_current(self):
        from app.engine import driver, game_state
        title = DB.constants.get('title').value
        driver.start(title, from_editor=True)
        game = game_state.start_level(self.current_level.nid)
        driver.run(game)

    def edit_preferences(self):
        dialog = PreferencesDialog(self)
        dialog.exec_()

    def about(self):
        QMessageBox.about(self, "About Lex Talionis Game Maker",
            "<p>This is the <b>Lex Talionis</b> Game Maker.</p>"
            "<p>Check out <a href='https://gitlab.com/rainlash/lex-talionis/wikis/home'>https://gitlab.com/rainlash/lex-talionis/wikis/home</a> "
            "for more information and helpful tutorials.</p>"
            "<p>This program has been freely distributed under the MIT License.</p>"
            "<p>Copyright 2014-2020 rainlash.</p>")

# Testing
# Run "python -m app.editor.main_editor" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainEditor()
    window.show()
    app.exec_()
