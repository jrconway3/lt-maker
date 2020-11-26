from PyQt5.QtCore import Qt

from app.data.database import DB

from app.editor.table_model import TableModel
from app.utilities import str_utils

from app.events.event_prefab import EventPrefab

class EventModel(TableModel):
    rows = ['nid', 'level_nid', 'trigger']

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:  # Row
            return '   '
        elif orientation == Qt.Horizontal:  # Column
            val = self.rows[idx]
            if val == 'nid':
                return 'ID'
            elif val == 'level_nid':
                return 'Level'
            else:
                return val.capitalize()
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            event = self._data[index.row()]
            str_attr = self.rows[index.column()]
            attr = getattr(event, str_attr)
            if str_attr == 'level_nid' and attr is None:
                return 'Global'
            return attr
        return None

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = str_utils.get_next_name("New Event", nids)
        new_event = EventPrefab(nid)
        DB.events.append(new_event)
        return new_event
