import os
import sys
import glob
from datetime import datetime
import json
import functools

from PyQt5.QtWidgets import QMainWindow, QAction, QMenu, QMessageBox, \
    QDockWidget, QFileDialog, QWidget, QLabel, QFrame, QDesktopWidget, \
    QToolButton, QWidgetAction, QStackedWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDir

from app.editor.settings import MainSettingsController

from app.constants import VERSION
from app.resources.resources import RESOURCES
from app.data.database import DB

from app.editor import timer

from app.editor.new_game_dialog import NewGameDialog

class ProjectFileBackend():
    def __init__(self, parent, app_state_manager):
        self.parent = parent
        self.app_state_manager = app_state_manager
        self.settings = MainSettingsController()
        self.current_proj = self.settings.get_current_project()
        timer.get_timer().autosave_timer.timeout.connect(self.autosave)

    def maybe_save(self):
        # if not self.undo_stack.isClean():
        if True:  # For now, since undo stack is not being used
            ret = QMessageBox.warning(self.parent, "Main Editor", "The current project may have been modified.\n"
                                            "Do you want to save your changes?",
                                            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def save(self, new=False):
        print("Save", self.current_proj, os.path.basename(self.current_proj))
        # check if we're editing default, if so, prompt to save as
        if os.path.basename(self.current_proj) == 'default.ltproj':
            self.current_proj = None
        if new or not self.current_proj:
            starting_path = self.current_proj or QDir.currentPath()
            fn, ok = QFileDialog.getSaveFileName(self.parent, "Save Project", starting_path,
                                                 "All Files (*)")
            if ok:
                if fn.endswith('.ltproj'):
                    self.current_proj = fn
                else:
                    self.current_proj = fn + '.ltproj'
                self.settings.set_current_project(self.current_proj)
            else:
                return False
            new = True

        if new:
            if os.path.exists(self.current_proj):
                ret = QMessageBox.warning(self.parent, "Save Project", "The file already exists.\nDo you want to overwrite it?",
                                          QMessageBox.Save | QMessageBox.Cancel)
                if ret == QMessageBox.Save:
                    pass
                else:
                    return False

        # Make directory for saving if it doesn't already exist
        if not os.path.isdir(self.current_proj):
            os.mkdir(self.current_proj)

        # Actually save project
        RESOURCES.save(self.current_proj)
        DB.serialize(self.current_proj)

        # Save metadata
        metadata_loc = os.path.join(self.current_proj, 'metadata.json')
        metadata = {}
        metadata['date'] = str(datetime.now())
        metadata['version'] = VERSION
        with open(metadata_loc, 'w') as serialize_file:
            json.dump(metadata, serialize_file, indent=4)

        # self.undo_stack.setClean()
        return True

    def new(self):
        if self.maybe_save():
            result = NewGameDialog.get()
            if result:
                identifier, title = result

                DB.load('default.ltproj')
                DB.constants.get('game_nid').set_value(identifier)
                DB.constants.get('title').set_value(title)
            return result
        return False

    def open(self):
        if self.maybe_save():
            starting_path = self.current_proj or QDir.currentPath()
            fn = QFileDialog.getExistingDirectory(
                self.parent, "Open Project Directory", starting_path)
            if fn:
                self.current_proj = fn
                self.settings.set_current_project(self.current_proj)
                self.load()
            else:
                return False
        return False

    def auto_open(self):
        path = self.settings.get_current_project()
        print("Auto Open: %s" % path)

        if path and os.path.exists(path):
            self.current_proj = path
            self.settings.set_current_project(self.current_proj)
            self.load()
            return True
        else:
            self.current_proj = "default.ltproj"
            self.settings.set_current_project(self.current_proj)
            self.load()
            return False

    def load(self):
        if os.path.exists(self.current_proj):
            RESOURCES.load(self.current_proj)
            DB.load(self.current_proj)
            # DB.init_load()

            # self.undo_stack.clear()

    def autosave(self):
        autosave_dir = os.path.abspath('autosave.ltproj')
        # Make directory for saving if it doesn't already exist
        if not os.path.isdir(autosave_dir):
            os.mkdir(autosave_dir)

        try:
            self.parent.status_bar.showMessage(
                'Autosaving project to %s...' % autosave_dir)
        except Exception:
            pass

        # Actually save project
        RESOURCES.save(autosave_dir)
        DB.serialize(autosave_dir)
