from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QGroupBox, \
    QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt

import app.data.ai as ai
from app.data.database import DB

from app.editor.custom_gui import PropertyBox, ComboBox
from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app import utilities

class AIDatabase(DatabaseDialog):
    @classmethod
    def create(cls, parent=None):
        data = DB.ai
        title = "AI"
        right_frame = AIProperties
        deletion_msg = "Cannot delete 'None' AI"
        creation_func = DB.create_new_ai
        collection_model = AIModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model, parent)
        return dialog

class AIModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            ai = self._data[index.row()]
            text = ai.nid
            return text
        return None

class BehaviourBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current = None

        self.layout = QHBoxLayout()

        self.action = ComboBox(self)
        for action in ai.AI_ActionTypes:
            self.action.addItem(action)
        self.action.currentIndexChanged.connect(self.action_changed)

        self.target = ComboBox(self)
        for target in ai.AI_TargetTypes:
            self.target.addItem(target)
        self.target.currentIndexChanged.connect(self.target_changed)

        self.view_range = ComboBox(self)
        self.view_range.setEditable(True)
        self.view_range.setInsertPolicy(QComboBox.NoInsert)
        self.view_range.addItem("Max Item Range")
        self.view_range.addItem("Movement + Max Item Range")
        self.view_range.addItem("Movement*2 + Max Item Range")
        self.view_range.addItem("Entire Map")
        self.view_range.lineEdit().editingFinished.connect(self.check_view_range)

        self.layout.addWidget(self.action)
        self.layout.addWidget(self.target)
        self.layout.addWidget(QLabel(" within "))
        self.layout.addWidget(self.view_range)
        self.setLayout(self.layout)

    def action_changed(self, index):
        action = self.action.currentText()
        self.current.action = action

    def target_changed(self, index):
        target = self.target.currentText()

    def check_view_range(self):
        cur_val = self.view_range.currentText()
        if utilities.is_int(cur_val):
            self.current.view_range = int(cur_val)
        else:
            self.current.view_range = -1 * self.view_range.currentIndex()

    def set_current(self, behaviour):
        self.current = behaviour

class AIProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        top_section.addWidget(self.nid_box)

        self.priority_box = PropertyBox("Priority", QSpinBox, self)
        self.priority_box.setToolTip("Higher priority AIs move first")
        self.priority_box.edit.setRange(0, 255)
        self.priority_box.edit.valueChanged.connect(self.priority_changed)
        top_section.addWidget(self.priority_box)

        main_section = QVBoxLayout()

        self.behaviour1 = BehaviourBox()
        self.behaviour2 = BehaviourBox()
        self.behaviour3 = BehaviourBox()

        main_section.addWidget(self.behaviour1)
        main_section.addWidget(self.behaviour2)
        main_section.addWidget(self.behaviour3)

        total_section = QVBoxLayout()
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        self.setLayout(total_section)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'AI ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()   

    def priority_changed(self, val):
        self.current.priority = int(val)

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.priority_box.edit.setValue(current.priority)
        if len(current.behaviours) > 0:
            self.behaviour1.set_current(current.behaviours[0])
        if len(current.behaviours) > 1:
            self.behaviour2.set_current(current.behaviours[1])
        if len(current.behaviours) > 2:
            self.behaviour3.set_current(current.behaviours[2])

# Testing
# Run "python -m app.editor.ai_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AIDatabase.create()
    window.show()
    app.exec_()
