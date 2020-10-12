from app.data.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.editor.data_editor import SingleDatabaseEditor

from app.editor.party_editor import party_model, party_properties

class PartyDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.parties
        title: str = "Party"
        right_frame = party_properties.PartyProperties

        collection_model = party_model.PartyModel
        return cls(data, title, right_frame, None, collection_model, parent)

# Run "python -m app.editor.party_editor.party_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(PartyDatabase)
    window.show()
    app.exec_()
