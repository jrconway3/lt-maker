from PyQt5.QtWidgets import QTableView

from app.data.database.database import DB

from app.editor.base_database_gui import DatabaseTab
from app.extensions.custom_gui import TableView
from app.editor.data_editor import SingleDatabaseEditor

from app.editor.event_editor import event_model, new_event_properties

class NewEventDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.events
        title: str = "Event"
        right_frame = new_event_properties.NewEventProperties

        collection_model = event_model.EventModel
        collection = new_event_properties.EventCollection
        dialog = cls(data, title, right_frame, None, collection_model, parent, view_type=QTableView, collection_type=collection)
        return dialog

# Testing
# Run "python -m app.editor.event_editor.new_event_tab"
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    DB.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    window = SingleDatabaseEditor(NewEventDatabase)
    window.show()
    app.exec_()
