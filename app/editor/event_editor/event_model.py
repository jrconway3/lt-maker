from PyQt5.QtCore import Qt

from app.data.database import DB

from app.editor.base_database_gui import DragDropCollectionModel
from app.utilities import str_utils

from app.events.event_prefab import EventPrefab

class EventModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            event = self._data[index.row()]
            text = event.nid
            return text
        return None

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = str_utils.get_next_name("New Event", nids)
        new_event = EventPrefab(nid)
        DB.events.append(new_event)
        return new_event
