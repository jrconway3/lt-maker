from PyQt5.QtWidgets import QWidget, QLineEdit, QCheckBox, \
    QSpinBox, QStyledItemDelegate, QVBoxLayout, QHBoxLayout

from app.data.database import DB
from app.data.supports import SupportRankRequirementList

from app.extensions.custom_gui import ComboBox, PropertyCheckBox
from app.editor.custom_widgets import UnitBox
from app.extensions.list_widgets import AppendMultiListWidget

class SupportPairProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        unit_section = QHBoxLayout()
        self.unit1_box = UnitBox(self)
        self.unit1_box.edit.currentIndexChanged.connect(self.unit1_changed)
        unit_section.addWidget(self.unit1_box)
        self.unit2_box = UnitBox(self)
        self.unit2_box.edit.currentIndexChanged.connect(self.unit2_changed)
        unit_section.addWidget(self.unit2_box)

        main_layout = QVBoxLayout()
        main_layout.addLayout(unit_section)

        self.one_way_box = PropertyCheckBox("One way?", QCheckBox, self)
        self.one_way_box.setToolTip("First unit gives bonuses to second unit")
        self.one_way_box.edit.stateChanged.connect(self.one_way_changed)
        main_layout.addWidget(self.one_way_box)

        attrs = ('support_rank', 'requirement', 'gate', 'damage', 'resist', 'accuracy', 'avoid', 'crit', 'dodge', 'attack_speed', 'defense_speed')
        self.rank_bonus = AppendMultiListWidget(
            SupportRankRequirementList(), "Rank Requirements & Personal Bonuses", 
            attrs, SupportRankRequirementDelegate, self)
        main_layout.addWidget(self.rank_bonus)
        self.setLayout(main_layout)

    def unit1_changed(self, index):
        self.current.unit1 = self.unit1_box.edit.currentText()

    def unit2_changed(self, index):
        self.current.unit2 = self.unit2_box.edit.currentText()

    def one_way_changed(self, state):
        self.current.one_way = bool(state)

    def set_current(self, current):
        self.current = current
        self.unit1_box.edit.setValue(current.unit1)
        self.unit2_box.edit.setValue(current.unit2)
        self.one_way_box.edit.setChecked(bool(current.one_way))
        self.rank_bonus.set_current(current.requirements)

class SupportRankRequirementDelegate(QStyledItemDelegate):
    rank_column = 0
    requirement_column = 1
    str_column = 2
    int_columns = (3, 4, 5, 6, 7, 8, 9, 10)

    def createEditor(self, parent, option, index):
        if index.column() in self.int_columns:
            editor = QSpinBox(parent)
            editor.setRange(-255, 255)
            return editor
        elif index.column() == self.requirement_column:
            editor = QSpinBox(parent)
            editor.setRange(0, 255)  # No negative rank unlocks allowed
            return editor
        elif index.column() == self.str_column:
            editor = QLineEdit(parent)
            return editor
        elif index.column() == self.rank_column:
            editor = ComboBox(parent)
            for rank in DB.support_ranks:
                editor.addItem(rank.rank)
            return editor
        else:
            return super().createEditor(parent, option, index)
