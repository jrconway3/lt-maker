import os

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSettings, QDir

from app.data.database import DB

from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab

from app.editor.item_editor import item_model, item_properties, item_import

class ItemDatabase(DatabaseTab):
    allow_import_from_lt = True

    @classmethod
    def create(cls, parent=None):
        data = DB.items
        title = "Item"
        right_frame = item_properties.ItemProperties
        deletion_criteria = None
        collection_model = item_model.ItemModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def import_data(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fn, ok = QFileDialog.getOpenFileName(self, "Import items from items.xml", starting_path, "Items XML (items.xml);;All Files(*)")
        if ok and fn.endswith('items.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.setValue("last_open_path", parent_dir)
            new_items = item_import.get_from_xml(parent_dir, fn)
            for item in new_items:
                self._data.append(item)
            self.update_list()

# Testing
# Run "python -m app.editor.item_editor.item_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(ItemDatabase)
    window.show()
    app.exec_()
