import os

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSettings, QDir

from app.data.database import DB
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab

from app.editor.unit_editor.unit_properties import UnitProperties
from app.editor.unit_editor.unit_model import UnitModel

class UnitDatabase(DatabaseTab):
    allow_import_from_lt = True

    @classmethod
    def create(cls, parent=None):
        data = DB.units
        title = "Unit"
        right_frame = UnitProperties
        deletion_criteria = (None, None, None)
        collection_model = UnitModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def import_data(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fn, ok = QFileDialog.getOpenFileName(self, "Import units from units.xml", starting_path, "Units XML (units.xml);;All Files(*)")
        if ok and fn.endswith('units.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.setValue("last_open_path", parent_dir)
            with open(fn) as units_xml:
                pass

# Testing
# Run "python -m app.editor.unit_editor.unit_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(UnitDatabase)
    window.show()
    app.exec_()
