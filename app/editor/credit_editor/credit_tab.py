from app.data.database.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.editor.data_editor import SingleDatabaseEditor

from app.editor.credit_editor import credit_model, credit_properties

class CreditDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.credit
        title: str = 'Credit'
        right_frame = credit_properties.CreditProperties

        collection_model = credit_model.CreditModel
        dialog = cls(data, title, right_frame, (None, None, None), collection_model, parent)
        return dialog

# Testing
# Run "python -m app.editor.credit_editor.credit_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    DB.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    window = SingleDatabaseEditor(CreditDatabase)
    window.show()
    app.exec_()
