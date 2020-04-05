from PyQt5.QtWidgets import QSpinBox, QComboBox, QDialog, QWidget, QHBoxLayout, \
    QLineEdit, QPushButton, QAction, QMenu, QSizePolicy, QFrame, \
    QDialogButtonBox, QListView, QTreeView, QItemDelegate, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QSize, QItemSelectionModel

class SimpleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        
    @classmethod
    def edit(cls, parent):
        dialog = cls(parent)
        dialog.exec_()

class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

class DeletionDialog(Dialog):
    def __init__(self, affected_items, model, msg, box, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deletion Warning")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.model = model(affected_items, parent)
        self.view = QListView(self)
        self.view.setModel(self.model)
        self.view.setSelectionMode(0)  # No selection
        self.view.setIconSize(QSize(32, 32))

        self.text1 = QLabel(msg)
        self.text2 = QLabel("Swap these references to:")
        self.box = box

        self.layout.addWidget(self.text1)
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.text2)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.buttonbox)

    @staticmethod
    def get_swap(affected_items, model, msg, box, parent=None):
        dialog = DeletionDialog(affected_items, model, msg, box, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.box.edit.currentIndex()
            return dialog.box.model._data[idx], True
        else:
            return None, False

    @staticmethod
    def get_simple_swap(affected_items, model, msg, box, parent=None):
        dialog = DeletionDialog(affected_items, model, msg, box, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.box.edit.currentIndex()
            return idx, True
        else:
            return None, False

class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)

class QVLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(1)

class ComboBox(QComboBox):
    def setValue(self, text):
        i = self.findText(text)
        if i >= 0:
            self.setCurrentIndex(i)

class LineSearch(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.line_edit = QLineEdit(self)
        self.line_edit.setReadOnly(True)
        self.search_button = QPushButton('...', self)
        self.search_button.setMaximumWidth(40)
        layout.setSpacing(0)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.search_button)
        self.setLayout(layout)

class PropertyBox(QWidget):
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label, self)
        self.label.setAlignment(Qt.AlignBottom)
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.edit = widget(self)
        self.edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.bottom_section = QHBoxLayout()
        self.bottom_section.addWidget(self.edit)

        layout.addWidget(self.label)
        layout.addLayout(self.bottom_section)

    def add_button(self, button):
        self.button = button
        self.bottom_section.addWidget(self.button)

class PropertyCheckBox(QWidget):
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # self.label = QLabel(label, self)
        # self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.edit = widget(label, self)
        self.edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(self.edit)
        # layout.addWidget(self.label)
        # layout.setAlignment(self.label, Qt.AlignLeft)

class RightClickView(object):
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
            delete_action = QAction("Delete", self, triggered=lambda: self.delete(index))
            menu.addAction(delete_action)
            if self.can_duplicate and not self.can_duplicate(self.model(), index):
                duplicate_action.setEnabled(False)
            if self.can_delete and not self.can_delete(self.model(), index):
                delete_action.setEnabled(False)
            
        menu.popup(self.viewport().mapToGlobal(pos))

    def new(self, index):
        idx = index.row()
        self.model().new(idx)
        self.setCurrentIndex(index)

    def duplicate(self, index):
        idx = index.row()
        self.model().duplicate(idx)
        self.setCurrentIndex(index)

    def delete(self, index):
        idx = index.row()
        self.model().delete(idx)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            indices = self.selectionModel().selectedIndexes()
            for index in indices:
                if not self.can_delete or self.can_delete(self.model(), index):
                    self.delete(index)

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        is_selected = self.selectionModel().isSelected(index)
        super().mousePressEvent(event)
        if not index.isValid() or is_selected:
            self.clearSelection()
            self.selectionModel().setCurrentIndex(index, QItemSelectionModel.Select)

class RightClickTreeView(RightClickView, QTreeView):
    pass

class RightClickListView(RightClickView, QListView):
    pass

class ResourceListView(RightClickView, QListView):
    def check_index(self, index):
        return True

    def customMenuRequested(self, pos):
        index = self.indexAt(pos)
        if not self.check_index(index):
            return

        menu = QMenu(self)
        new_action = QAction("New", self, triggered=lambda: self.new(index))
        menu.addAction(new_action)

        # Check to see if we're actually selecting something
        if index.isValid():
            rename_action = QAction("Rename", self, triggered=lambda: self.edit(index))
            menu.addAction(rename_action)
            delete_action = QAction("Delete", self, triggered=lambda: self.delete(index))
            menu.addAction(delete_action)
            if self.can_rename and not self.can_rename(self.model(), index):
                rename_action.setEnabled(False)
            if self.can_delete and not self.can_delete(self.model(), index):
                delete_action.setEnabled(False)

        menu.popup(self.viewport().mapToGlobal(pos))

class ResourceTreeView(ResourceListView):
    def check_index(self, index):
        item = index.internalPointer()
        if item.parent_image:
            return False
        return True

    # def keyPressEvent(self, event):
    #     RightClickView.keyPressEvent(self, event)

class IntDelegate(QItemDelegate):
    def __init__(self, parent, int_columns):
        super().__init__(parent)
        self.int_columns = int_columns

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setAlignment(Qt.AlignRight)
            editor.setRange(-1023, 1023)
            return editor
        else:
            return super().createEditor(parent, option, index)
