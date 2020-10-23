import os

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSettings, QDir

from app.data.database import DB
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab

from app.editor.class_editor import class_model, class_properties, class_import

class ClassDatabase(DatabaseTab):
    allow_import_from_lt = True
    
    @classmethod
    def create(cls, parent=None):
        data = DB.classes
        title = "Class"
        right_frame = class_properties.ClassProperties

        def deletion_func(model, index):
            return model._data[index.row()].nid != "Citizen"

        collection_model = class_model.ClassModel
        dialog = cls(data, title, right_frame, (deletion_func, None, deletion_func), collection_model, parent)
        return dialog

    def tick(self):
        self.update_list()

    def import_data(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fn, ok = QFileDialog.getOpenFileName(self, "Import units from units.xml", starting_path, "Units XML (units.xml);;All Files(*)")
        if ok and fn.endswith('units.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.setValue("last_open_path", parent_dir)
            new_units = class_import.get_from_xml(parent_dir, fn)
            for unit in new_units:
                self._data.append(unit)
            self.update_list()

# Testing
# Run "python -m app.editor.unit_editor.unit_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app import dark_theme
    d = dark_theme.QDarkBGPalette()
    d.set_app(app)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(ClassDatabase)
    # MEME
    window.setStyleSheet("QDialog {background-image:url(bg.png)};")
    window.show()
    app.exec_()
