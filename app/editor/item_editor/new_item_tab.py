from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFileDialog)

import app.engine.item_component_access as ICA
from app.data.database.items import ItemCatalog, ItemPrefab
from app.editor import timer
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.item_editor import item_import, item_model
from app.editor.item_skill_properties import NewComponentProperties
from app.editor.settings.main_settings_controller import MainSettingsController
from app.editor.component_object_editor import ComponentObjectEditor

class NewItemProperties(NewComponentProperties[ItemPrefab]):
    title = "Item"
    get_components = staticmethod(ICA.get_item_components)
    get_templates = staticmethod(ICA.get_templates)
    get_tags = staticmethod(ICA.get_item_tags)


class NewItemDatabase(ComponentObjectEditor):
    catalog_type = ItemCatalog

    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewItemDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

    @property
    def data(self):
        return self._db.items

    def get_icon(self, item_nid) -> Optional[QIcon]:
        pix = item_model.get_pixmap(self.data.get(item_nid))
        if pix:
            return QIcon(pix.scaled(32, 32))
        return None

    def import_csv(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fn, ok = QFileDialog.getOpenFileName(self, "Import items from csv", starting_path, "items csv (*.csv);;All Files(*)")
        if ok and fn:
            parent_dir = os.path.split(fn)[0]
            settings.set_last_open_path(parent_dir)
            item_import.update_db_from_csv(self._db, fn)
            self.reset()