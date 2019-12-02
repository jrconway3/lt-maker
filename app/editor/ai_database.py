from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QGroupBox, QRadioButton, \
    QVBoxLayout, QComboBox, QStackedWidget
from PyQt5.QtCore import Qt

import app.data.ai as ai
from app.data.database import DB

from app.editor.custom_gui import get_icon, PropertyBox, ComboBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app import utilities

class AIDatabase(DatabaseTab):
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

class NullSpecification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QHBoxLayout()

        self.setLayout(self.layout)

    def set_current(self, target_spec):
        pass

class UnitSpecification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QHBoxLayout()
        self.box1 = ComboBox(self)
        for spec in ai.unit_spec:
            self.box1.addItem(spec)
        self.box1.currentIndexChanged.connect(self.unit_spec_changed)

        self.box2 = ComboBox(self)
        self.box2.currentIndexChanged.connect(self.sub_spec_changed)

        self.layout.addWidget(self.box1)
        self.layout.addWidget(self.box2)

        self.setLayout(self.layout)

    def unit_spec_changed(self, index):
        unit_spec = self.box1.currentText()
        self.box2.setEnabled(True)
        self.box2.clear()
        if unit_spec == "Class":
            for klass in DB.classes:
                icon = get_icon(klass, (80, 72))
                if icon:
                    self.box2.addItem(icon, klass.nid)
                else:
                    self.box2.addItem(klass.nid)
        elif unit_spec == "Tag":
            self.box2.addItems(DB.tags)
        elif unit_spec == "ID":
            self.box2.addItems(DB.units.keys())
        elif unit_spec == "Name":
            self.box2.addItems([unit.name for unit in DB.units])
        elif unit_spec == "Faction":
            for faction in DB.factions:
                icon = get_icon(faction, (32, 32))
                if icon:
                    self.box2.addItem(icon, faction.nid)
                else:
                    self.box2.addItem(icon, faction.nid)
        else:
            self.box2.setEnabled(False)

    def sub_spec_changed(self, index):
        unit_spec = self.box1.currentText()
        sub_spec = self.box2.currentText()
        self.window.current.target_spec = (unit_spec, sub_spec)

    def set_current(self, target_spec):
        self.box1.setValue(target_spec[0])
        self.box2.setValue(target_spec[1])

class EventSpecification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QHBoxLayout()
        self.box = ComboBox(self)
        for spec in ai.event_types:
            self.box.addItem(spec)
        self.box.currentIndexChanged.connect(self.spec_changed)

        self.layout.addWidget(self.box)
        self.setLayout(self.layout)

    def spec_changed(self, index):
        event = self.box.currentText()
        self.window.current.target_spec = event

    def set_current(self, target_spec):
        self.box.setValue(target_spec)

class PositionSpecification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.layout = QVBoxLayout()
        self.starting = QRadioButton("Starting", self)
        self.starting.toggled.connect(self.starting_toggled)
        self.custom = QRadioButton("Custom", self)

        bottom = QHBoxLayout()
        bottom.addWidget(self.custom)
        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        self.x_spinbox.setMinimumWidth(40)
        self.y_spinbox.setMinimumWidth(40)
        self.x_spinbox.setRange(0, 255)
        self.y_spinbox.setRange(0, 255)
        self.x_spinbox.setEnabled(False)
        self.y_spinbox.setEnabled(False)
        self.x_spinbox.valueChanged.connect(self.change_spinbox)
        self.y_spinbox.valueChanged.connect(self.change_spinbox)
        bottom.addWidget(self.x_spinbox)
        bottom.addWidget(self.y_spinbox)

        self.layout.addWidget(self.starting)
        self.layout.addLayout(bottom)

        self.setLayout(self.layout)

    def starting_toggled(self, checked):
        if checked:
            self.x_spinbox.setEnabled(False)
            self.y_spinbox.setEnabled(False)
            self.window.current.target_spec = "Starting"
        else:
            self.x_spinbox.setEnabled(True)
            self.y_spinbox.setEnabled(True)
            x, y = self.x_spinbox.value(), self.y_spinbox.value()
            self.window.current.target_spec = (x, y)

    def change_spinbox(self, value):
        x, y = self.x_spinbox.value(), self.y_spinbox.value()
        self.window.current.target_spec = (x, y)

    def set_current(self, target_spec):
        if target_spec == "Starting":
            self.starting.setChecked(True)
        else:
            self.starting.setChecked(False)
            self.x_spinbox.setValue(target_spec[0])
            self.y_spinbox.setValue(target_spec[1])

class BehaviourBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current = None

        self.layout = QHBoxLayout()

        self.action = ComboBox(self)
        for action in ai.AI_ActionTypes:
            self.action.addItem(action.replace('_', ' '))
        self.action.currentIndexChanged.connect(self.action_changed)

        self.target = ComboBox(self)
        for target in ai.AI_TargetTypes:
            self.target.addItem(target)
        self.target.currentIndexChanged.connect(self.target_changed)

        self.target_spec = QStackedWidget(self)
        for target in ai.AI_TargetTypes:
            if target == "None":
                target_spec = NullSpecification(self)
            elif target in ("Unit", "Ally", "Enemy"):
                target_spec = UnitSpecification(self)
            elif target == "Position":
                target_spec = PositionSpecification(self)
            elif target == "Tile":
                target_spec = NullSpecification(self)
            elif target == "Event":
                target_spec = EventSpecification(self)
            self.target_spec.addWidget(target_spec)

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
        self.layout.addWidget(self.target_spec)
        self.layout.addWidget(QLabel(" within "))
        self.layout.addWidget(self.view_range)
        self.setLayout(self.layout)

    def action_changed(self, index):
        action = self.action.currentText()
        self.current.action = action

    def target_changed(self, index):
        target = self.target.currentText().replace(' ', '_')
        self.current.target = target
        # Swap the specification
        idx = ai.AI_TargetTypes.index(self.current.target)
        self.target_spec.setCurrentIndex(idx)

    def check_view_range(self):
        cur_val = self.view_range.currentText()
        if utilities.is_int(cur_val):
            self.current.view_range = int(cur_val)
        else:
            self.current.view_range = -1 * self.view_range.currentIndex()

    def set_current(self, behaviour):
        self.current = behaviour
        self.action.setValue(behaviour.action)
        self.target.setValue(behaviour.target)
        target_spec = self.target_spec.currentWidget()
        target_spec.set_current(behaviour.target_spec)
        if behaviour.view_range < 0:
            correct_index = -behaviour.view_range - 1
            self.view_range.setCurrentIndex(correct_index)
        else:
            self.view_range.setEditText(str(behaviour.view_range))

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

        self.behaviour1 = PropertyBox("Behaviour 1", BehaviourBox, self)
        self.behaviour2 = PropertyBox("Behaviour 2", BehaviourBox, self)
        self.behaviour3 = PropertyBox("Behaviour 3", BehaviourBox, self)
        self.behaviour_boxes = [self.behaviour1, self.behaviour2, self.behaviour3]

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
        for idx, behaviour in enumerate(current.behaviours):
            self.behaviour_boxes[idx].edit.set_current(behaviour)

# Testing
# Run "python -m app.editor.ai_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AIDatabase.create()
    window.show()
    app.exec_()
