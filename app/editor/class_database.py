from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QDialog, QSplitter, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QDoubleSpinBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.weapons import WexpGainList
from app.data.skills import LearnedSkillList
from app.data.database import DB

from app.editor.custom_gui import PropertyBox, ComboBox, QHLine
from app.editor.multi_select_combo_box import MultiSelectComboBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.misc_dialogs import TagDialog, StatDialog
from app.editor.sub_list_widget import AppendMultiListWidget, BasicMultiListWidget
from app.editor.stat_widget import ClassStatWidget
from app.editor.weapon_database import WexpGainDelegate
from app.editor.skill_database import LearnedSkillDelegate
from app.editor.icons import ItemIcon80
from app import utilities

class ClassDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.classes
        title = "Class"
        right_frame = ClassProperties
        deletion_msg = "Cannot delete Citizen Class!"
        creation_func = DB.create_new_class
        collection_model = ClassModel
        dialog = cls(data, title, right_frame, deletion_msg, creation_func, collection_model, parent)
        return dialog

class ClassModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            klass = self._data[index.row()]
            text = klass.nid
            return text
        elif role == Qt.DecorationRole:
            klass = self._data[index.row()]
            x, y = klass.icon_index
            pixmap = QPixmap(klass.icon_fn).copy(x*80, y*72, 80, 72)
            if pixmap.width() > 0 and pixmap.height > 0:
                return QIcon(pixmap)
            else:
                return None
        return None

class ClassProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon80(None, self)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.short_name_box = PropertyBox("Short Display Name", QLineEdit, self)
        self.short_name_box.edit.setMaxLength(10)
        self.short_name_box.edit.textChanged.connect(self.short_name_changed)
        name_section.addWidget(self.short_name_box)

        self.long_name_box = PropertyBox("Display Name", QLineEdit, self)
        self.long_name_box.edit.setMaxLength(20)
        self.long_name_box.edit.textChanged.connect(self.long_name_changed)
        name_section.addWidget(self.long_name_box)

        top_section.addLayout(name_section)

        main_section = QGridLayout()

        self.desc_box = PropertyBox("Description", QLineEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)
        main_section.addWidget(self.desc_box, 0, 0, 1, 3)

        self.movement_box = PropertyBox("Movement Type", ComboBox, self)
        self.movement_box.edit.addItems(DB.mcost.get_movement_types())
        self.movement_box.edit.currentIndexChanged.connect(self.movement_changed)
        main_section.addWidget(self.movement_box, 0, 3)

        self.tier_box = PropertyBox("Tier", QSpinBox, self)
        self.tier_box.edit.setRange(0, 5)
        self.tier_box.edit.setAlignment(Qt.AlignRight)
        self.tier_box.edit.valueChanged.connect(self.tier_changed)
        main_section.addWidget(self.tier_box, 1, 0)

        self.promotes_from_box = PropertyBox("Promotes From", ComboBox, self)
        self.promotes_from_box.edit.addItems(["None"] + DB.classes.keys())
        self.promotes_from_box.edit.currentIndexChanged.connect(self.promotes_from_changed)
        main_section.addWidget(self.promotes_from_box, 1, 1, 1, 2)

        self.max_level_box = PropertyBox("Max Level", QSpinBox, self)
        self.max_level_box.edit.setRange(1, 255)
        self.max_level_box.edit.setAlignment(Qt.AlignRight)
        self.max_level_box.edit.valueChanged.connect(self.max_level_changed)
        main_section.addWidget(self.max_level_box, 1, 3)

        tag_section = QHBoxLayout()

        self.turns_into_box = PropertyBox("Turns Into", MultiSelectComboBox, self)
        self.turns_into_box.edit.setPlaceholderText("Promotion Options...")
        self.turns_into_box.edit.addItems(DB.classes.keys())
        self.turns_into_box.edit.updated.connect(self.turns_into_changed)
        tag_section.addWidget(self.turns_into_box)

        self.tag_box = PropertyBox("Tags", MultiSelectComboBox, self)
        self.tag_box.edit.setPlaceholderText("No tag")
        self.tag_box.edit.addItems(DB.tags)
        self.tag_box.edit.updated.connect(self.tags_changed)
        tag_section.addWidget(self.tag_box)

        self.tag_box.add_button(QPushButton('...'))
        self.tag_box.button.setMaximumWidth(40)
        self.tag_box.button.clicked.connect(self.access_tags)

        stat_section = QGridLayout()

        self.class_stat_widget = ClassStatWidget(self.current, "Stats", self)
        self.class_stat_widget.button.clicked.connect(self.access_stats)
        stat_section.addWidget(self.class_stat_widget, 1, 0, 1, 2)

        weapon_section = QHBoxLayout()

        attrs = ("usable", "weapon_type", "wexp_gain")
        self.wexp_gain_widget = BasicMultiListWidget(WexpGainList([], DB.weapons), "Weapon Exp.", attrs, WexpGainDelegate, self)
        self.wexp_gain_widget.model.checked_columns = {0}  # Add checked column
        weapon_section.addWidget(self.wexp_gain_widget)

        skill_section = QHBoxLayout()

        attrs = ("level", "skill_nid")
        self.class_skill_widget = AppendMultiListWidget(LearnedSkillList(), "Class Skills", attrs, LearnedSkillDelegate, self)
        skill_section.addWidget(self.class_skill_widget)

        exp_section = QHBoxLayout()

        self.exp_mult_box = PropertyBox("Exp Multiplier", QDoubleSpinBox, self)
        self.exp_mult_box.edit.setAlignment(Qt.AlignRight)
        self.exp_mult_box.edit.setDecimals(1)
        self.exp_mult_box.edit.setSingleStep(0.1)
        self.exp_mult_box.edit.setRange(0, 255)
        self.exp_mult_box.edit.valueChanged.connect(self.exp_mult_changed)
        exp_section.addWidget(self.exp_mult_box)

        self.opp_exp_mult_box = PropertyBox("Opponent Exp Multiplier", QDoubleSpinBox, self)
        self.opp_exp_mult_box.edit.setAlignment(Qt.AlignRight)
        self.opp_exp_mult_box.edit.setDecimals(1)
        self.opp_exp_mult_box.edit.setSingleStep(0.1)
        self.opp_exp_mult_box.edit.setRange(0, 255)
        self.opp_exp_mult_box.edit.valueChanged.connect(self.opp_exp_mult_changed)
        exp_section.addWidget(self.opp_exp_mult_box)

        total_section = QVBoxLayout()
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addLayout(tag_section)
        total_section.addWidget(QHLine())
        total_section.addLayout(stat_section)
        total_section.addLayout(exp_section)
        total_widget = QWidget()
        total_widget.setLayout(total_section)

        right_section = QVBoxLayout()
        right_section.addLayout(weapon_section)
        right_section.addWidget(QHLine())
        right_section.addLayout(skill_section)
        right_widget = QWidget()
        right_widget.setLayout(right_section)

        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(total_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setStyleSheet("QSplitter::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc); border: 1px solid #777; width: 13px; margin-top: 2px; margin-bottom: 2px; border-radius: 4px;}")

        final_section = QHBoxLayout()
        self.setLayout(final_section)
        final_section.addWidget(self.splitter)

        # final_section = QHBoxLayout()
        # self.setLayout(final_section)
        # final_section.addLayout(total_section)
        # final_section.addWidget(QVLine())
        # final_section.addLayout(right_section)

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Class ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def short_name_changed(self, text):
        self.current.short_name = text

    def long_name_changed(self, text):
        self.current.long_name = text

    def desc_changed(self, text):
        self.current.desc = text

    def tier_changed(self, val):
        self.current.tier = val

    def promotes_from_changed(self, index):
        p = self.promotes_from_box.edit.currentText()
        if p == "None":
            self.current.promotes_from = None
        else:
            self.current.promotes_from = p

    def movement_changed(self, index):
        self.movement_group = self.movement_box.edit.currentText()

    def max_level_changed(self, val):
        self.current.max_level = val

    def turns_into_changed(self):
        self.current.turns_into = self.turns_into_box.edit.currentText()

    def tags_changed(self):
        self.current.tags = self.tag_box.edit.currentText()

    def exp_mult_changed(self):
        self.current.exp_mult = float(self.exp_mult_box.edit.text())

    def opp_exp_mult_changed(self):
        self.current.opponent_exp_mult = float(self.opp_exp_mult_box.edit.text())

    def access_tags(self):
        dlg = TagDialog.create()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.tag_box.edit.clear()
            self.tag_box.edit.addItems(DB.tags)
            self.tag_box.edit.setCurrentTexts(self.current.tags)
        else:
            pass

    def access_stats(self):
        dlg = StatDialog.create()
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.class_stat_widget.update_stats()
        else:
            pass

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.short_name_box.edit.setText(current.short_name)
        self.long_name_box.edit.setText(current.long_name)
        self.desc_changedbox.edit.setText(current.desc)
        self.tier_box.edit.setValue(current.tier)
        self.max_level_box.edit.setValue(current.max_level)
        self.movement_box.edit.setValue(current.movement_group)
        if current.promotes_from:
            self.promotes_from_box.edit.setValue(current.promotes_from)
        else:
            self.promotes_from_box.edit.setValue("None")
        self.turns_into_box.edit.ResetSelection()
        self.turns_into_box.edit.setCurrentTexts(current.turns_into)
        self.tag_box.edit.ResetSelection()
        self.tag_box.edit.setCurrentTexts(current.tags)

        self.class_stat_widget.set_new_obj(current)

        self.exp_mult_box.edit.setValue(self.current.exp_mult)
        self.opp_exp_mult_box.edit.setValue(self.current.opponent_exp_mult)

        self.class_skill_widget.set_current(self.current.skills)
        self.wexp_gain_widget.set_current(self.current.wexp_gain)

# Testing
# Run "python -m app.editor.class_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ClassDatabase.create()
    window.show()
    app.exec_()
