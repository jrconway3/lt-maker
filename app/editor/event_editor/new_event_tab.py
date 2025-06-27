from typing import Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTableView, QMessageBox

from app.data.database.database import DB

from app.editor.new_editor_tab import NewEditorTab
from app.editor.data_editor import SingleDatabaseEditor

from app.editor.event_editor import event_model, new_event_properties
from app.events.event_prefab import EventCatalog
from app.extensions.custom_gui import DeletionTab, DeletionDialog
from app.utilities.typing import NID

class NewEventDatabase(NewEditorTab):
    catalog_type = EventCatalog
    properties_type = new_event_properties.NewEventProperties

    @property
    def data(self):
        return self._db.events

    def get_icon(self, class_nid: NID) -> Optional[QIcon]:
        return None

    def create_new(self, nid):
        if self.data.get(nid):
            QMessageBox.warning(self, 'Warning', 'ID %s already in use' % nid)
            return False
        new_event = self.catalog_type.datatype(nid, nid, '')
        self.data.append(new_event)
        return True

    def _on_nid_changed(self, old_nid: NID, new_nid: NID):
        return True

    def _on_delete(self, nid: NID) -> bool:
        return True

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
