from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QGroupBox, QRadioButton, \
    QVBoxLayout, QComboBox, QStackedWidget
from PyQt5.QtCore import Qt

import app.data.ai as ai
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox
from app.editor.custom_widgets import ClassBox, UnitBox, FactionBox
from app.utilities import str_utils

# Target Specifications
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

        self.box2 = QStackedWidget(self)
        self.box2.addWidget(ComboBox(self))
        class_box = ClassBox(self)
        class_box.edit.currentIndexChanged.connect(self.sub_spec_changed)
        self.box2.addWidget(class_box)
        tag_box = ComboBox(self)
        tag_box.addItems([tag.nid for tag in DB.tags])
        tag_box.currentIndexChanged.connect(self.sub_spec_changed)
        self.box2.addWidget(tag_box)
        name_box = ComboBox(self)
        name_box.addItems([unit.name for unit in DB.units])
        name_box.currentIndexChanged.connect(self.sub_spec_changed)
        self.box2.addWidget(name_box)
        faction_box = FactionBox(self)
        faction_box.edit.currentIndexChanged.connect(self.sub_spec_changed)
        self.box2.addWidget(faction_box)
        unit_box = UnitBox(self)
        unit_box.edit.currentIndexChanged.connect(self.sub_spec_changed)
        self.box2.addWidget(unit_box)

        self.layout.addWidget(self.box1)
        self.layout.addWidget(self.box2)

        self.setLayout(self.layout)

    def unit_spec_changed(self, index):
        unit_spec = self.box1.currentText()
        self.box2.setEnabled(True)
        if unit_spec == "Class":
            self.box2.setCurrentIndex(1)
        elif unit_spec == "Tag":
            self.box2.setCurrentIndex(2)
        elif unit_spec == "Name":
            self.box2.setCurrentIndex(3)
        elif unit_spec == "Faction":
            self.box2.setCurrentIndex(4)
        elif unit_spec == "ID":
            self.box2.setCurrentIndex(5)
        else:
            self.box2.setCurrentIndex(0)
            self.box2.setEnabled(False)

    def sub_spec_changed(self, index):
        unit_spec = self.box1.currentText()
        sub_spec = self.box2.currentWidget().currentText()
        self.window.current.target_spec = (unit_spec, sub_spec)

    def set_current(self, target_spec):
        if target_spec:
            self.box1.setValue(target_spec[0])
            self.box2.currentWidget().setValue(target_spec[1])
        else:
            self.box1.setValue("All")
            self.box2.setEnabled(False)

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
            x, y = int(self.x_spinbox.value()), int(self.y_spinbox.value())
            self.window.current.target_spec = (x, y)

    def change_spinbox(self, value):
        x, y = int(self.x_spinbox.value()), int(self.y_spinbox.value())
        self.window.current.target_spec = (x, y)

    def set_current(self, target_spec):
        print("Set Current target spec", flush=True)
        print(target_spec, flush=True)
        if target_spec == ["Starting"] or target_spec == "Starting":
            self.window.current.target_spec = "Starting"
            self.starting.setChecked(True)
        else:
            self.starting.setChecked(False)
            self.x_spinbox.setValue(int(target_spec[0]))
            self.y_spinbox.setValue(int(target_spec[1]))

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
        action = self.action.currentText().replace(' ', '_')
        self.current.action = action

    def target_changed(self, index):
        print("target_changed")
        target = self.target.currentText()
        print(target)
        if target == 'None':
            print("Set Target Spec to None")
            self.current.target = 'None'
            self.target_spec.setCurrentIndex(0)
            return
        self.current.target[0] = target
        # Swap the specification
        idx = ai.AI_TargetTypes.index(target)
        self.target_spec.setCurrentIndex(idx)
        print(self.current.target[0])
        print(index, flush=True)

    def check_view_range(self):
        cur_val = self.view_range.currentText()
        if str_utils.is_int(cur_val):
            self.current.view_range = int(cur_val)
        else:
            self.current.view_range = -1 * self.view_range.currentIndex()

    def set_current(self, behaviour):
        self.current = behaviour
        print("Behaviour Set Current")
        print(behaviour.action)
        print(behaviour.target)
        action = behaviour.action.replace('_', ' ')
        self.action.setValue(action)
        if behaviour.action in ('Move_to', 'Move_away_from'):
            self.target.show()
            print(behaviour.target[0])
            print(behaviour.target[1])
            self.target.setValue(behaviour.target[0])
            target_spec = self.target_spec.currentWidget()
            print(behaviour.target[1], flush=True)
            target_spec.set_current(behaviour.target[1])
        else:
            print("Target Set Value None")
            self.target.setValue('None')
            self.target_spec.setCurrentIndex(0)
            self.target.hide()
            if behaviour.action in ('Attack', 'Support', 'Steal'):
                self.target_spec.setCurrentIndex(1)  # Units
                target_spec = self.target_spec.currentWidget()
                target_spec.set_current(behaviour.target)
            elif behaviour.action == 'Interact':
                self.target_spec.setCurrentIndex(5)  # Event
                target_spec = self.target_spec.currentWidget()
                target_spec.set_current(behaviour.target)

        if behaviour.view_range < 0:
            correct_index = -behaviour.view_range - 1
            self.view_range.setCurrentIndex(correct_index)
        else:
            self.view_range.setEditText(str(behaviour.view_range))

class AIProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self.model = self.window.left_frame.model
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
        self.priority_box.edit.setAlignment(Qt.AlignRight)
        self.priority_box.edit.valueChanged.connect(self.priority_changed)
        top_section.addWidget(self.priority_box)

        main_section = QVBoxLayout()

        self.behaviour1 = BehaviourBox(self)
        self.behaviour1.setTitle("Behaviour 1")
        self.behaviour2 = BehaviourBox(self)
        self.behaviour2.setTitle("Behaviour 2")
        self.behaviour3 = BehaviourBox(self)
        self.behaviour3.setTitle("Behaviour 3")
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
            self.current.nid = str_utils.get_next_name(self.current.nid, other_nids)
        self.model.change_nid(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()   

    def priority_changed(self, val):
        self.current.priority = int(val)

    def set_current(self, current):
        self.current = current
        print("AI Current")
        print(current.nid)
        self.nid_box.edit.setText(current.nid)
        self.priority_box.edit.setValue(current.priority)
        for idx, behaviour in enumerate(current.behaviours):
            self.behaviour_boxes[idx].set_current(behaviour)
