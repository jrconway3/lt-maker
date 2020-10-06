from app.data.database import DB
from app.editor.base_database_gui import DatabaseTab

from app.editor.unit_editor.unit_properties import UnitProperties
from app.editor.unit_editor.unit_model import UnitModel

class UnitDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.units
        title = "Unit"
        right_frame = UnitProperties
        deletion_criteria = (None, None, None)
        collection_model = UnitModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

# Testing
# Run "python -m app.editor.unit_editor.unit_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    DB.load('default.ltproj')
    window = UnitDatabase.create()
    window.show()
    app.exec_()
