import os

from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5.QtCore import QSettings, QDir

from app.data.database import DB
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab

from app.editor.unit_editor import unit_model, unit_properties, unit_import

class UnitDatabase(DatabaseTab):
    allow_import_from_lt = True

    @classmethod
    def create(cls, parent=None):
        data = DB.units
        title = "Unit"
        right_frame = unit_properties.UnitProperties
        deletion_criteria = (None, None, None)
        collection_model = unit_model.UnitModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def import_data(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fn, ok = QFileDialog.getOpenFileName(self, "Import units from units.xml", starting_path, "Units XML (units.xml);;All Files(*)")
        if ok and fn.endswith('units.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.setValue("last_open_path", parent_dir)
            new_units = unit_import.get_from_xml(parent_dir, fn)
            for unit in new_units:
                self._data.append(unit)
            self.update_list()

def get():
    window = SingleDatabaseEditor(UnitDatabase)
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_unit = window.tab.right_frame.current
        return selected_unit, True
    else:
        return None, False
                
# Testing
# Run "python -m app.editor.unit_editor.unit_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app import dark_theme
    d = dark_theme.QDarkPalette()
    d.set_app(app)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(UnitDatabase)
    window.show()
    app.exec_()
