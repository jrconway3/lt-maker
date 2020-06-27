from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout, \
    QGraphicsView, QGraphicsScene, QMessageBox
from PyQt5.QtCore import Qt, QDir, QAbstractItemModel, QModelIndex, QSettings
from PyQt5.QtGui import QPixmap, QIcon

import os

from app.resources.icons import Icon
from app.resources.resources import RESOURCES
from app.data.data import Data
from app.data.database import DB
from app.extensions.custom_gui import ResourceTreeView, DeletionDialog
from app.editor.base_database_gui import DatabaseTab

from app import utilities

class Icon16Display(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons16
        title = "16x16 Icon"
        right_frame = Icon16Properties
        collection_model = Icon16Model
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceTreeView)
        return dialog

class Icon32Display(Icon16Display):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons32
        title = "32x32 Icon"
        right_frame = Icon32Properties
        collection_model = Icon32Model
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceTreeView)
        return dialog

class Icon80Display(Icon16Display):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons80
        title = "80x72 Icon"
        right_frame = Icon80Properties
        collection_model = Icon80Model
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceTreeView)
        return dialog

class IconTreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        return None

    def index(self, row, column=0, parent_index=QModelIndex()):
        if not self.hasIndex(row, column, parent_index):
            return QModelIndex()
        if parent_index.isValid():
            parent_item = parent_index.internalPointer()
            child_item = parent_item.sub_images[row]
        else:
            child_item = self._data[row]
        
        return self.createIndex(row, column, child_item)

    def parent(self, child_index):
        if not child_index.isValid():
            return QModelIndex()
        child_item = child_index.internalPointer()
        parent_item = child_item.parent_image
        if parent_item:
            row_in_parent = parent_item.sub_images.index(child_item)
            return self.createIndex(row_in_parent, 0, parent_item)
        else:
            return QModelIndex()

    def rowCount(self, parent_index=None):
        if parent_index and parent_index.isValid():
            parent_item = parent_index.internalPointer()
            return len(parent_item.sub_images)
        else:
            return len(self._data)

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            text = item.nid
            return text
        elif role == Qt.DecorationRole:
            item = index.internalPointer()
            if item.pixmap:
                pixmap = item.pixmap.scaled(32, 32)
                return QIcon(pixmap)
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            if value:
                item = index.internalPointer()
                old_nid = item.nid
                nid = utilities.get_next_name(value, [d.nid for d in self._data])
                self._data.update_nid(item, nid)
                # Update nid of slices
                for image_resource in item.sub_images:
                    # Just for aesthetics, since everything actually refers to parent elsewhere
                    x, y = image_resource.icon_index
                    image_resource.nid = nid + " " + str(x) + ',' + str(y)
                self.nid_change_watchers(item, old_nid, nid)
                self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item.parent_image:  # Child item
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.NoItemFlags

    def delete(self, index):
        item = index.internalPointer()
        if item.parent_image:
            QMessageBox.critical(self.window, 'Error', "Can't delete child item!")
        else:
            self.layoutAboutToBeChanged.emit()
            self._data.delete(item)
            self.layoutChanged.emit()

    def create_new(self):
        raise NotImplementedError

    def append(self):
        self.create_new()
        view = self.window.view
        # self.dataChanged.emit(self.index(0), self.index(self.rowCount()))
        self.layoutChanged.emit()
        last_index = self.index(self.rowCount() - 1)
        view.setCurrentIndex(last_index)
        self.update_watchers(self.rowCount() - 1)
        return last_index

    def new(self, index):
        item = index.internalPointer()
        if item.parent_image:
            QMessageBox.critical(self.window, 'Error', "Cannot create new image slice!")
        else:
            idx = self._data.index(item.nid)
            self.create_new()
            self._data.move_index(len(self._data) - 1, idx + 1)
            self.layoutChanged.emit()
            self.update_watchers(self.rowCount() - 1)

    def update_watchers(self, idx):
        pass

    def nid_change_watchers(self, icon, old_nid, new_nid):
        pass

class Icon16Model(IconTreeModel):
    database = RESOURCES.icons16
    width, height = 16, 16

    def create_new(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Choose %s", starting_path, "PNG Files (*.png);;All Files(*)")
        if ok:
            for fn in fns:
                if fn.endswith('.png'):
                    nid = os.path.split(fn)[-1][:-4]  # Get rid of .png ending
                    pix = QPixmap(fn)
                    if pix.width() % self.width == 0 and pix.height() % self.height == 0:
                        nid = utilities.get_next_name(nid, [d.nid for d in self.database])
                        icon = Icon(nid, fn, pix)
                        self.database.append(icon)
                        icon_slice(icon, self.width, self.height)
                    else:
                        QMessageBox.critical(self.window, "File Size Error!", "Icon width and height must be exactly divisible by %dx%d pixels!" % (self.width, self.height))
                else:
                    QMessageBox.critical(self.window, "File Type Error!", "Icon must be PNG format!")
            parent_dir = os.path.split(fns[-1])[0]
            settings.setValue("last_open_path", parent_dir)

    def delete(self, index):
        icon = index.internalPointer()
        if icon.parent_image:
            QMessageBox.critical(self.window, 'Error', "Can't delete child item!")
        else:
            nid = icon.nid
            # What uses 16x16 icons
            # Items, Weapons, (Later on Affinities, Skills/Statuses)
            affected_items = [item for item in DB.items if item.icon_nid == nid]
            affected_weapons = [weapon for weapon in DB.weapons if weapon.icon_nid == nid]
            if affected_items or affected_weapons:
                if affected_items:
                    affected = Data(affected_items)
                    from app.editor.item_database import ItemModel
                    model = ItemModel
                elif affected_weapons:
                    affected = Data(affected_weapons)
                    from app.editor.weapon_database import WeaponModel
                    model = WeaponModel
                msg = "Deleting Icon <b>%s</b> would affect these objects."
                ok = DeletionDialog.inform(affected, model, msg, self.window)
                if ok:
                    pass
                else:
                    return
            self.layoutAboutToBeChanged.emit()
            self._data.delete(icon)
            # self.dataChanged.emit()
            self.layoutChanged.emit()

    def nid_change_watchers(self, icon, old_nid, new_nid):
        # What uses 16x16 icons
        # Items, Weapons, (Later on Affinities, Skills/Statuses)
        for item in DB.items:
            if item.icon_nid == old_nid:
                item.icon_nid = new_nid
        for weapon in DB.weapons:
            if weapon.icon_nid == old_nid:
                weapon.icon_nid = new_nid

class Icon32Model(Icon16Model):
    database = RESOURCES.icons32
    width, height = 32, 32

    def delete(self, index):
        icon = index.internalPointer()
        if icon.parent_image:
            QMessageBox.critical(self.window, 'Error', "Can't delete child item!")
        else:
            nid = icon.nid
            # What uses 32x32 icons
            # Factions
            affected_factions = [faction for faction in DB.factions if faction.icon_nid == nid]
            if affected_factions:
                affected = Data(affected_factions)
                from app.editor.faction_database import FactionModel
                model = FactionModel
                msg = "Deleting Icon <b>%s</b> would affect these factions."
                ok = DeletionDialog.inform(affected, model, msg, self.window)
                if ok:
                    pass
                else:
                    return
            self.layoutAboutToBeChanged.emit()
            self._data.delete(icon)
            self.layoutChanged.emit()

    def nid_change_watchers(self, icon, old_nid, new_nid):
        # What uses 32x32 icons
        # Factions
        for faction in DB.factions:
            if faction.icon_nid == old_nid:
                faction.icon_nid = new_nid

class Icon80Model(Icon16Model):
    database = RESOURCES.icons80
    width, height = 80, 72

    def delete(self, index):
        icon = index.internalPointer()
        if icon.parent_image:
            QMessageBox.critical(self.window, 'Error', "Can't delete child item!")
        else:
            nid = icon.nid
            # What uses 80x72 icons
            # Classes
            affected_classes = [klass for klass in DB.classes if klass.icon_nid == nid]
            if affected_classes:
                affected = Data(affected_classes)
                from app.editor.class_database import ClassModel
                model = ClassModel
                msg = "Deleting Icon <b>%s</b> would affect these classes."
                ok = DeletionDialog.inform(affected, model, msg, self.window)
                if ok:
                    pass
                else:
                    return
            self.layoutAboutToBeChanged.emit()
            self._data.delete(icon)
            self.layoutChanged.emit()

    def nid_change_watchers(self, icon, old_nid, new_nid):
        # What uses 80x72 icons
        # Classes
        for klass in DB.classes:
            if klass.icon_nid == old_nid:
                klass.icon_nid = new_nid

class IconView(QGraphicsView):
    min_scale = 0.5
    max_scale = 5
    static_size = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setMouseTracking(True)

        self.image = None
        self.screen_scale = 1

    def set_image(self, pixmap):
        if pixmap:
            self.image = pixmap
            if not self.static_size:
                self.setSceneRect(0, 0, self.image.width(), self.image.height())
        else:
            self.image = None
            self.clear_scene()

    def clear_scene(self):
        self.scene.clear()

    def show_image(self):
        if self.image:
            self.clear_scene()
            self.scene.addPixmap(self.image)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self.screen_scale < self.max_scale:
            self.screen_scale += 1
            self.scale(2, 2)
        elif event.angleDelta().y() < 0 and self.screen_scale > self.min_scale:
            self.screen_scale -= 1
            self.scale(0.5, 0.5)

def icon_slice(resource, base_width, base_height):
    sheet = resource.pixmap
    width, height = sheet.width(), sheet.height()
    # if width == base_width and height == base_height:
    #     return
    resource.sub_images.clear()
    for x in range(width//base_width):
        for y in range(height//base_height):
            region = sheet.copy(x*base_width, y*base_height, base_width, base_height)
            new_nid = resource.nid + " " + str(x) + ',' + str(y)
            new_image = Icon(new_nid, resource.full_path, region)
            new_image.icon_index = (x, y)
            resource.sub_images.append(new_image)
            new_image.parent_image = resource

class Icon16Properties(QWidget):
    width, height = 16, 16

    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for resource in self._data:
            resource.pixmap = QPixmap(resource.full_path)

        for resource in list(self._data.values()):
            icon_slice(resource, self.width, self.height)
            
        self.current = current

        self.view = IconView(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.view)

    def set_current(self, current):
        self.current = current
        self.view.set_image(self.current.pixmap)
        self.view.show_image()

class Icon32Properties(Icon16Properties):
    width, height = 32, 32

class Icon80Properties(Icon16Properties):
    width, height = 80, 72
