from PyQt5.QtWidgets import QApplication, QAction, QMenu, QTreeView
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from app import utilities
from app.data.data import Data

class GroupTag():
    def __init__(self, nid):
        self.nid = nid
        self.collection = []

class GroupingModel(QAbstractItemModel):
    """
    Supports drag and drop
    """
    drop_to = None

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.tags = Data()
        # Organize Tags
        unique_tags = sorted({d.tag for d in self._data if d.tag})
        for tag in unique_tags:
            self.tags.append(GroupTag(tag))
        self.tags.append(GroupTag("Untagged"))
        for d in self._data:
            if d.tag:
                group = self.tags.get(d.tag)
            else:
                group = self.tags.get("Untagged")
            group.collection.append(d.nid)

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        return None

    def index(self, row, column=0, parent_index=QModelIndex()):
        if not self.hasIndex(row, column, parent_index):
            return QModelIndex()
        if parent_index.isValid():
            parent_item = parent_index.internalPointer()
            nid = parent_item.collection[row]
            child_item = self._data.get(nid)
        else:
            child_item = self.tags[row]

        return self.createIndex(row, column, child_item)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        if isinstance(child_item, GroupTag):
            return QModelIndex()
        else:
            parent_group_nid = child_item.tag if child_item.tag else "Untagged"
            parent_item = self.tags.get(parent_group_nid)
            if parent_item:
                row_in_parent = parent_item.collection.index(child_item.nid)
                return self.createIndex(row_in_parent, 0, parent_item)
            else:
                return QModelIndex()

    def rowCount(self, parent_index=None):
        if parent_index and parent_index.isValid():
            parent_item = parent_index.internalPointer()
            if isinstance(parent_item, GroupTag):
                return len(parent_item.collection)
            else:  # No children for lowest level thingamajig
                return 0
        else:
            return len(self.tags)

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        raise NotImplementedError

    def setData(self, index, role):
        return False

    def flags(self, index):
        if index.isValid():
            item = index.internalPointer()
            if isinstance(item, GroupTag):  # Parent Item
                return Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            else:
                return Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif index.row() >= len(self._data) or index.model() is not self:
            return Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def insertRows(self, row, count, parent):
        if count < 1 or row < 0 or row > self.rowCount() or parent.isValid():
            return False
        self.drop_to = row
        self.layoutChanged.emit()
        return True

    def do_drag_drop(self, idx):
        if self.drop_to is None:
            return False
        if idx < self.drop_to:
            self._data.move_index(idx, self.drop_to - 1)
            return idx, self.drop_to - 1
        else:
            self._data.move_index(idx, self.drop_to)
            return idx, self.drop_to

    def removeRows(self, row, count, parent):
        if count < 1 or row < 0 or (row + count) > self.rowCount() or parent.isValid():
            return False
        result = self.do_drag_drop(row)
        self.layoutChanged.emit()
        if result:
            self.update_drag_watchers(*result)
        return True

    def delete(self, index):
        item = index.internalPointer()
        self.layoutAboutToBeChanged.emit()
        if isinstance(item, GroupTag):  # Parent Item
            # Move all data in collection to untagged
            for subitem in item.collection:
                subitem.tag = None
            self.tags.delete(item)
        else:    
            self.delete_item(item)
        self.layoutChanged.emit()

    def delete_item(self, item):
        print("Deleting %s" % item.nid)
        tag = item.tag if item.tag else "Untagged"
        collection = self.tags.get(tag).collection
        collection.remove(item.nid)
        self._data.delete(item)

    def duplicate(self, index):
        item = index.internalPointer()
        self.layoutAboutToBeChanged.emit()
        if isinstance(item, GroupTag):
            new_nid = utilities.get_next_name(item.nid, [t.nid for t in self.tags])
            self.tags.insert(index.row() + 1, (GroupTag(new_nid)))
        else:
            pass
        self.layoutChanged.emit()

    def create_new(self):
        raise NotImplementedError

    def append(self):
        self.create_new()
        view = self.window.view
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1)
        view.setCurrentIndex(last_index)
        self.update_watchers(self.rowCount() - 1)
        return last_index

    def new(self, index):
        item = index.internalPointer()
        if isinstance(item, GroupTag):
            self.tags.append("New Group")
            self.layoutChanged.emit()
        else:
            idx = self._data.index(item.nid)
            self.create_new()
            view = self.window.view
            self._data.move_index(len(self._data) - 1, idx + 1)
            self.layoutChanged.emit()
            new_index = self._data[idx + 1]
            view.setCurrentIndex(new_index)
            self.update_watchers(self.rowCount() - 1)

    def update_watchers(self, idx):
        pass

    def update_drag_watchers(self, fro, to):
        pass

    def nid_change_watchers(self, item, old_nid, new_nid):
        pass

class GroupingView(QTreeView):
    def __init__(self, action_funcs=None, parent=None):
        super().__init__(parent)
        self.window = parent

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(4)  # QAbstractItemView.InternalMove

        if action_funcs:
            self.can_delete, self.can_duplicate, self.can_rename = action_funcs
        else:
            self.can_delete, self.can_duplicate, self.can_rename = None, None, None

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenuRequested)

    def customMenuRequested(self, pos):
        index = self.indexAt(pos)
        menu = QMenu(self)

        new_action = QAction("New", self, triggered=lambda: self.new(index))
        menu.addAction(new_action)
        # Check to see if we're actually selecting something
        if index.isValid():
            print(self.can_delete, self.can_duplicate, self.can_rename, flush=True)
            duplicate_action = QAction("Duplicate", self, triggered=lambda: self.duplicate(index))
            menu.addAction(duplicate_action)
            rename_action = QAction("Rename", self, triggered=lambda: self.edit(index))
            menu.addAction(rename_action)
            delete_action = QAction("Delete", self, triggered=lambda: self.delete(index))
            menu.addAction(delete_action)
            item = index.internalPointer()
            is_group_tag = isinstance(item, GroupTag)
            if not is_group_tag and self.can_duplicate and not self.can_duplicate(self.model(), index):
                duplicate_action.setEnabled(False)
            if not is_group_tag and self.can_delete and not self.can_delete(self.model(), index):
                delete_action.setEnabled(False)
            if not is_group_tag and self.can_rename and not self.can_rename(self.model(), index):
                rename_action.setEnabled(False)
            
        menu.popup(self.viewport().mapToGlobal(pos))

    def new(self, index):
        new_index = self.model().new(index)
        if new_index:
            self.setCurrentIndex(new_index)

    def duplicate(self, index):
        new_index = self.model().duplicate(index)
        if new_index:
            self.setCurrentIndex(new_index)

    def delete(self, index):
        self.model().delete(index)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            indices = self.selectionModel().selectedIndexes()
            for index in indices:
                item = index.internalPointer()
                is_group_tag = isinstance(item, GroupTag)
                if not is_group_tag and not self.can_delete or self.can_delete(self.model(), index):
                    self.delete(index)
        elif event.key() == Qt.Key_D and (QApplication.keyboardModifiers() & Qt.ControlModifier):
            indices = self.selectionModel().selectedIndexes()
            for index in indices:
                item = index.internalPointer()
                is_group_tag = isinstance(item, GroupTag)
                if not is_group_tag and not self.can_duplicate or self.can_duplicate(self.model(), index):
                    self.duplicate(index)
        elif event.key() == Qt.Key_N and (QApplication.keyboardModifiers() & Qt.ControlModifier):
            indices = self.selectionModel().selectedIndexes()
            for index in indices:
                self.new(index)
