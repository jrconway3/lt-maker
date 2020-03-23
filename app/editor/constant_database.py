import math

from PyQt5.QtWidgets import QGridLayout, QLineEdit, QSpinBox, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QTreeView, QWidget, QDoubleSpinBox, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QAbstractItemModel

from app.data.data import Data
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox

from app.editor.base_database_gui import DatabaseTab
from app.editor.component_database import ComponentModel

class BoolConstantsModel(ComponentModel):
    def __init__(self, data, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.window = parent
        self._data = data

    def data(self, index, role):
        if not index.isValid():
            return None
        data = self._data[index.row()]
        if role == Qt.DisplayRole:
            return data.name
        elif role == Qt.CheckStateRole:
            value = Qt.Checked if data.value else Qt.Unchecked
            return value
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            data = self._data[index.row()]
            if value == Qt.Checked:
                data.value = True
            else:
                data.value = False
            self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemNeverHasChildren | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return basic_flags

class MainExpEquation(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        label = QLabel('Combat Experience Equation:', self)
        label.setAlignment(Qt.AlignBottom)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(label)

        exp_magnitude = self._data.get('exp_magnitude')
        self.exp_magnitude = QDoubleSpinBox(self)
        self.exp_magnitude.setValue(exp_magnitude.value)
        self.exp_magnitude.setDecimals(1)
        self.exp_magnitude.setRange(0, 255)
        self.exp_magnitude.valueChanged.connect(exp_magnitude.set_value)
        exp_curve = self._data.get('exp_curve')
        self.exp_curve = QDoubleSpinBox(self)
        self.exp_curve.setValue(exp_curve.value)
        self.exp_curve.setDecimals(3)
        self.exp_curve.setRange(0, 255)
        self.exp_curve.valueChanged.connect(exp_curve.set_value)
        exp_offset = self._data.get('exp_offset')
        self.exp_offset = QDoubleSpinBox(self)
        self.exp_offset.setValue(exp_offset.value)
        self.exp_offset.setDecimals(1)
        self.exp_offset.setRange(-255, 255)
        self.exp_offset.valueChanged.connect(exp_offset.set_value)

        self.exp_magnitude.valueChanged.connect(self.window.parameters_changed)
        self.exp_curve.valueChanged.connect(self.window.parameters_changed)
        self.exp_offset.valueChanged.connect(self.window.parameters_changed)

        label1 = QLabel(' * e^(', self)
        label2 = QLabel(' * (<b>Level Difference</b> + ', self)
        label3 = QLabel('))', self)

        eq_layout = QHBoxLayout()
        eq_layout.setAlignment(Qt.AlignHCenter)
        eq_layout.setSpacing(0)
        eq_layout.setContentsMargins(0, 0, 0, 0)
        eq_layout.addWidget(self.exp_magnitude)
        eq_layout.addWidget(label1)
        eq_layout.addWidget(self.exp_curve)
        eq_layout.addWidget(label2)
        eq_layout.addWidget(self.exp_offset)
        eq_layout.addWidget(label3)
        layout.addLayout(eq_layout)

class DisplayExpResults(QWidget):
    @classmethod
    def create(cls, data, parent=None):
        text = 'A level ', ' unit fights a level ', ' unit'
        return cls(data, text, parent)

    def __init__(self, data, text, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        self.level1 = QSpinBox(self)
        self.level1.setValue(1)
        self.level1.setRange(1, 255)
        self.level1.setMaximumWidth(60)
        self.level1.setAlignment(Qt.AlignRight)
        self.level1.valueChanged.connect(self.update_parameters)
        
        self.level2 = QSpinBox(self)
        self.level2.setValue(10)
        self.level2.setRange(1, 255)
        self.level2.setMaximumWidth(60)
        self.level2.setAlignment(Qt.AlignRight)
        self.level2.valueChanged.connect(self.update_parameters)

        self.label1 = QLabel(text[0], self)
        self.label2 = QLabel(text[1], self)
        self.label3 = QLabel(text[2], self)

        self.label4 = QLabel('Experience Gained: ', self)
        self.label4.setAlignment(Qt.AlignBottom)
        self.label4.setAlignment(Qt.AlignRight)

        self.edit_box = QLineEdit(self)
        self.edit_box.setMaximumWidth(100)
        self.edit_box.setReadOnly(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignHCenter)
        hlayout.setSpacing(0)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(self.label1)
        hlayout.addWidget(self.level1)
        hlayout.addWidget(self.label2)
        hlayout.addWidget(self.level2)
        hlayout.addWidget(self.label3)
        layout.addLayout(hlayout)

        hlayout2 = QHBoxLayout()
        hlayout2.setAlignment(Qt.AlignHCenter)
        hlayout2.setSpacing(0)
        hlayout2.setContentsMargins(0, 0, 0, 0)
        hlayout2.addWidget(self.label4)
        hlayout2.addWidget(self.edit_box)
        layout.addLayout(hlayout2)

        self.update_parameters()

    # def resizeEvent(self, event):
    #     print("Wow", flush=True)
    #     super().resizeEvent(event)

    #     self.label1.move(0, 0)
    #     self.level1.move(self.label1.width(), 0)
    #     running_width = self.label1.width() + self.level1.width()
    #     self.label2.move(running_width, 0)
    #     running_width += self.label2.width()
    #     self.level2.move(running_width, 0)
    #     running_width += self.level2.width()
    #     self.label3.move(running_width, 0)

    #     self.label4.move(0, self.label1.height() + 4)
    #     self.edit_box.move(self.label4.width(), self.label1.height() + 4)

    def update_parameters(self, val=None):
        level_diff = self.level2.value() - self.level1.value() + self._data.get('exp_offset').value
        exp_gained = self._data.get('exp_magnitude').value * math.exp(level_diff * self._data.get('exp_curve').value)
        exp_gained = max(self._data.get('min_exp').value, exp_gained)
        display = str(int(exp_gained)) + " (" + str(round(exp_gained, 2)) + ")"
        self.edit_box.setText(display)

class DisplayHealExpResults(DisplayExpResults):
    @classmethod
    def create(cls, data, parent=None):
        text = 'A level ', ' unit heals ', ' damage'
        return cls(data, text, parent)

    def update_parameters(self, val=None):
        heal_diff = self.level2.value() - self.level1.value() + self._data.get('heal_offset').value
        exp_gained = (self._data.get('heal_curve').value * heal_diff) + self._data.get('heal_magnitude').value
        exp_gained = max(self._data.get('heal_min').value, exp_gained)
        display = str(int(exp_gained)) + " (" + str(round(exp_gained, 2)) + ")"
        self.edit_box.setText(display)

class HealExpEquation(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        label = QLabel('Heal Experience Equation:', self)
        label.setAlignment(Qt.AlignBottom)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(label)

        heal_magnitude = self._data.get('heal_magnitude')
        self.heal_magnitude = QSpinBox(self)
        self.heal_magnitude.setValue(heal_magnitude.value)
        self.heal_magnitude.setRange(-255, 255)
        self.heal_magnitude.valueChanged.connect(heal_magnitude.set_value)
        heal_curve = self._data.get('heal_curve')
        self.heal_curve = QDoubleSpinBox(self)
        self.heal_curve.setValue(heal_curve.value)
        self.heal_curve.setDecimals(3)
        self.heal_curve.setRange(0, 255)
        self.heal_curve.valueChanged.connect(heal_curve.set_value)
        heal_offset = self._data.get('heal_offset')
        self.heal_offset = QDoubleSpinBox(self)
        self.heal_offset.setValue(heal_offset.value)
        self.heal_offset.setDecimals(1)
        self.heal_offset.setRange(-255, 255)
        self.heal_offset.valueChanged.connect(heal_offset.set_value)

        self.heal_magnitude.valueChanged.connect(self.window.parameters_changed)
        self.heal_curve.valueChanged.connect(self.window.parameters_changed)
        self.heal_offset.valueChanged.connect(self.window.parameters_changed)

        label1 = QLabel(' * (<b>Amount Healed - Level</b> + ', self)
        label2 = QLabel(') + ', self)
        label3 = QLabel(')', self)

        eq_layout = QHBoxLayout()
        eq_layout.setAlignment(Qt.AlignHCenter)
        eq_layout.setSpacing(0)
        eq_layout.setContentsMargins(0, 0, 0, 0)
        eq_layout.addWidget(self.heal_curve)
        eq_layout.addWidget(label1)
        eq_layout.addWidget(self.heal_offset)
        eq_layout.addWidget(label2)
        eq_layout.addWidget(self.heal_magnitude)
        eq_layout.addWidget(label3)
        layout.addLayout(eq_layout)

class ExperienceWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        layout = QGridLayout()
        self.setLayout(layout)

        self.main_exp_equation = MainExpEquation(data, self)
        layout.addWidget(self.main_exp_equation, 0, 0, 1, 3)

        min_exp = data.get('min_exp')
        self.min_exp = PropertyBox(min_exp.name, QSpinBox, self)
        self.min_exp.edit.setRange(0, 100)
        self.min_exp.edit.setValue(min_exp.value)
        self.min_exp.edit.setAlignment(Qt.AlignRight)
        self.min_exp.edit.valueChanged.connect(min_exp.set_value)
        self.min_exp.edit.valueChanged.connect(self.parameters_changed)

        kill_multiplier = data.get('kill_multiplier')
        self.kill_multiplier = PropertyBox(kill_multiplier.name, QDoubleSpinBox, self)
        self.kill_multiplier.edit.setRange(0, 10)
        self.kill_multiplier.edit.setDecimals(1)
        self.kill_multiplier.edit.setAlignment(Qt.AlignRight)
        self.kill_multiplier.edit.setValue(kill_multiplier.value)
        self.kill_multiplier.edit.valueChanged.connect(kill_multiplier.set_value)
        self.kill_multiplier.edit.valueChanged.connect(self.parameters_changed)

        boss_bonus = data.get('boss_bonus')
        self.boss_bonus = PropertyBox(boss_bonus.name, QSpinBox, self)
        self.boss_bonus.edit.setRange(0, 255)
        self.boss_bonus.edit.setAlignment(Qt.AlignRight)
        self.boss_bonus.edit.setValue(boss_bonus.value)
        self.boss_bonus.edit.valueChanged.connect(boss_bonus.set_value)
        self.boss_bonus.edit.valueChanged.connect(self.parameters_changed)

        layout.addWidget(self.min_exp, 1, 0)
        layout.addWidget(self.kill_multiplier, 1, 1)
        layout.addWidget(self.boss_bonus, 1, 2)

        self.display_exp = DisplayExpResults.create(data, self)
        layout.addWidget(self.display_exp, 2, 0, 1, 3)

    def parameters_changed(self, val):
        self.display_exp.update_parameters()

class MiscExperienceWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        layout = QGridLayout()
        self.setLayout(layout)

        self.main_exp_equation = HealExpEquation(data, self)
        layout.addWidget(self.main_exp_equation, 0, 0, 1, 3)

        self.display_exp = DisplayHealExpResults.create(data, self)
        layout.addWidget(self.display_exp, 1, 0, 1, 3)

        heal_min = data.get('heal_min')
        self.heal_min = PropertyBox(heal_min.name, QSpinBox, self)
        self.heal_min.edit.setRange(0, 100)
        self.heal_min.edit.setValue(heal_min.value)
        self.heal_min.edit.setAlignment(Qt.AlignRight)
        self.heal_min.edit.valueChanged.connect(heal_min.set_value)
        self.heal_min.edit.valueChanged.connect(self.parameters_changed)

        default_exp = data.get('default_exp')
        self.default_exp = PropertyBox(default_exp.name, QSpinBox, self)
        self.default_exp.edit.setRange(0, 100)
        self.default_exp.edit.setAlignment(Qt.AlignRight)
        self.default_exp.edit.setValue(default_exp.value)
        self.default_exp.edit.valueChanged.connect(default_exp.set_value)
        self.default_exp.edit.valueChanged.connect(self.parameters_changed)

        steal_exp = data.get('steal_exp')
        self.steal_exp = PropertyBox(steal_exp.name, QSpinBox, self)
        self.steal_exp.edit.setRange(0, 100)
        self.steal_exp.edit.setAlignment(Qt.AlignRight)
        self.steal_exp.edit.setValue(steal_exp.value)
        self.steal_exp.edit.valueChanged.connect(steal_exp.set_value)
        self.steal_exp.edit.valueChanged.connect(self.parameters_changed)

        layout.addWidget(self.heal_min, 2, 0)
        layout.addWidget(self.default_exp, 2, 1)
        layout.addWidget(self.steal_exp, 2, 2)

    def parameters_changed(self, val):
        self.display_exp.update_parameters()

class ConstantDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.constants
        title = "Constants"

        dialog = cls(data, title, parent)
        return dialog

    def update_list(self):
        pass

    def reset(self):
        pass

    # Now we get to the new stuff
    def __init__(self, data, title, parent=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = data
        self.title = title

        self.setWindowTitle('%s Editor' % self.title)
        self.setStyleSheet("font: 10pt")

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        bool_section = QGroupBox(self)
        bool_constants = Data([d for d in self._data if d.attr == bool])
        bool_model = BoolConstantsModel(bool_constants, self)
        bool_view = QTreeView()
        bool_view.setModel(bool_model)
        bool_view.header().hide()

        bool_layout = QHBoxLayout()
        bool_section.setLayout(bool_layout)
        bool_layout.addWidget(bool_view)

        battle_constants = ('num_items', 'num_accessories', 'min_damage', 'unarmed_disadvantage', 'enemy_leveling', 'rng')
        battle_section = self.create_section(battle_constants)
        battle_section.setTitle("Battle Constants")
        misc_constants = ('title', 'steal', 'num_save_slots')
        misc_section = self.create_section(misc_constants)
        misc_section.setTitle("Miscellaneous Constants")

        exp_section = QGroupBox(self)
        exp_layout = QVBoxLayout()
        exp_section.setLayout(exp_layout)
        exp_widget = ExperienceWidget(self._data, self)
        exp_layout.addWidget(exp_widget)
        exp_section.setTitle("Combat Experience Constants")

        heal_section = QGroupBox(self)
        heal_layout = QVBoxLayout()
        heal_section.setLayout(heal_layout)
        heal_widget = MiscExperienceWidget(self._data, self)
        heal_layout.addWidget(heal_widget)
        heal_section.setTitle("Miscellaneous Experience Constants")

        self.layout.addWidget(battle_section, 0, 0)
        self.layout.addWidget(misc_section, 0, 1)
        self.layout.addWidget(exp_section, 1, 0, 1, 2)
        self.layout.addWidget(heal_section, 2, 0, 1, 2)
        self.layout.addWidget(bool_section, 0, 2, 3, 1)

    def create_section(self, constants):
        section = QGroupBox(self)
        layout = QVBoxLayout()
        section.setLayout(layout)
        
        for constant_nid in constants:
            constant = self._data.get(constant_nid)
            if not constant:
                print("Couldn't find constant %s" % constant_nid)
                continue
            if constant.attr == int:
                box = PropertyBox(constant.name, QSpinBox, self)
                box.edit.setRange(0, 10)
                box.edit.setValue(constant.value)
                box.edit.valueChanged.connect(constant.set_value)
            elif constant.attr == str:
                box = PropertyBox(constant.name, QLineEdit, self)
                box.edit.setText(constant.value)
                box.edit.textChanged.connect(constant.set_value)
            else: # Choice tuple
                box = PropertyBox(constant.name, ComboBox, self)
                box.edit.addItems(constant.attr)
                box.edit.setValue(constant.value)
                box.edit.currentTextChanged.connect(constant.set_value)
            layout.addWidget(box)
        return section

        # self.layout.addWidget()
