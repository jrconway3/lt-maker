from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QDialog, QSplitter, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QDoubleSpinBox, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

from app.data.weapons import WexpGainData
from app.data.skills import LearnedSkillList
from app.data.resources import RESOURCES
from app.data.data import Data
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox, QHLine, DeletionDialog
from app.extensions.list_widgets import AppendMultiListWidget, BasicMultiListWidget
from app.extensions.multi_select_combo_box import MultiSelectComboBox

from app.editor.timer import TIMER 

from app.editor.custom_widgets import ClassBox
from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app.editor.tag_widget import TagDialog
from app.editor.stat_widget import StatListWidget
from app.editor.weapon_database import WexpGainDelegate
from app.editor.skill_database import LearnedSkillDelegate
import app.editor.map_sprite_display as map_sprite_display
from app.editor.icons import ItemIcon80
from app.editor.resource_editor import ResourceEditor

from app import utilities

class ClassDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.classes
        title = "Class"
        right_frame = ClassProperties

        def deletion_func(model, index):
            return model._data[index.row()].nid != "Citizen"

        collection_model = ClassModel
        dialog = cls(data, title, right_frame, (deletion_func, None, deletion_func), collection_model, parent)
        return dialog

    def tick(self):
        self.update_list()

def get_map_sprite_icon(klass, num=0, current=False, team='player', gender=0):
    if gender >= 5:
        res = RESOURCES.map_sprites.get(klass.female_map_sprite_nid)
    else:
        res = RESOURCES.map_sprites.get(klass.male_map_sprite_nid)
    if not res:
        return None
    if not res.standing_pixmap:
        res.standing_pixmap = QPixmap(res.standing_full_path)
    pixmap = res.standing_pixmap
    pixmap = map_sprite_display.get_basic_icon(pixmap, num, current, team)
    return pixmap

class ClassModel(DragDropCollectionModel):
    display_team = 'player'

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            klass = self._data[index.row()]
            text = klass.nid
            return text
        elif role == Qt.DecorationRole:
            klass = self._data[index.row()]
            num = TIMER.passive_counter.count
            if hasattr(self.window, 'view'):
                active = index == self.window.view.currentIndex()
            else:
                active = False
            pixmap = get_map_sprite_icon(klass, num, active, self.display_team)
            # Fallback to female map sprite nid
            if not pixmap:
                pixmap = get_map_sprite_icon(klass, num, active, self.display_team, gender=5)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        return None

    def delete(self, idx):
        # check to make sure nothing else is using me!!!
        klass = self._data[idx]
        nid = klass.nid
        affected_units = [unit for unit in DB.units if unit.klass == nid]
        affected_classes = [k for k in DB.classes if k.promotes_from == nid or nid in k.turns_into]
        affected_ais = [ai for ai in DB.ai if 
                        any(behaviour.target_spec and 
                            behaviour.target_spec[0] == "Class" and 
                            behaviour.target_spec[1] == nid 
                            for behaviour in ai.behaviours)]
        affected_levels = [level for level in DB.levels if any(unit.klass == nid for unit in level.units)]
        if affected_units or affected_classes or affected_ais or affected_levels:
            if affected_units:
                affected = Data(affected_units)
                from app.editor.unit_database import UnitModel
                model = UnitModel
            elif affected_classes:
                affected = Data(affected_classes)
                from app.editor.class_database import ClassModel
                model = ClassModel
            elif affected_ais:
                affected = Data(affected_ais)
                from app.editor.ai_database import AIModel
                model = AIModel
            elif affected_levels:
                affected = Data(affected_levels)
                from app.editor.level_menu import LevelModel
                model = LevelModel
            msg = "Deleting Class <b>%s</b> would affect these objects" % nid
            swap, ok = DeletionDialog.get_swap(affected, model, msg, ClassBox(self.window, exclude=klass), self.window)
            if ok:
                self.change_nid(nid, swap.nid)
            else:
                return
        # Delete watchers
        super().delete(idx)

    def change_nid(self, old_nid, new_nid):
        for unit in DB.units:
            if unit.klass == old_nid:
                unit.klass = new_nid
        for k in DB.classes:
            if k.promotes_from == old_nid:
                k.promotes_from = new_nid
            k.turns_into = [new_nid if elem == old_nid else elem for elem in k.turns_into]
        for ai in DB.ai:
            for behaviour in ai.behaviours:
                if behaviour.target_spec and behaviour.target_spec[0] == "Class" and behaviour.target_spec[1] == old_nid:
                    behaviour.target_spec[1] = new_nid
        for level in DB.levels:
            for unit in level.units:
                if unit.klass == old_nid:
                    unit.klass = new_nid

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New Class", nids)
        DB.create_new_class(nid, name)

class ClassProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self.model = self.window.left_frame.model
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon80(self)
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
        self.tag_box.edit.addItems(DB.tags.keys())
        self.tag_box.edit.updated.connect(self.tags_changed)
        tag_section.addWidget(self.tag_box)

        self.tag_box.add_button(QPushButton('...'))
        self.tag_box.button.setMaximumWidth(40)
        self.tag_box.button.clicked.connect(self.access_tags)

        stat_section = QGridLayout()

        self.class_stat_widget = StatListWidget(self.current, "Stats", self)
        # self.class_stat_widget.button.clicked.connect(self.access_stats)
        stat_section.addWidget(self.class_stat_widget, 1, 0, 1, 2)

        weapon_section = QHBoxLayout()

        attrs = ("usable", "weapon_type", "wexp_gain")
        self.wexp_gain_widget = BasicMultiListWidget(WexpGainData.from_xml([], DB.weapons), "Weapon Exp.", attrs, WexpGainDelegate, self)
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

        self.male_map_sprite_label = QLabel()
        self.male_map_sprite_label.setMaximumWidth(32)
        self.male_map_sprite_box = QPushButton("Choose Male Map Sprite...")
        self.male_map_sprite_box.clicked.connect(self.select_male_map_sprite)

        self.female_map_sprite_label = QLabel()
        self.female_map_sprite_label.setMaximumWidth(32)
        self.female_map_sprite_box = QPushButton("Choose Female Map Sprite...")
        self.female_map_sprite_box.clicked.connect(self.select_female_map_sprite)

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
        male_section = QHBoxLayout()
        male_section.addWidget(self.male_map_sprite_label)
        male_section.addWidget(self.male_map_sprite_box)
        right_section.addLayout(male_section)
        female_section = QHBoxLayout()
        female_section.addWidget(self.female_map_sprite_label)
        female_section.addWidget(self.female_map_sprite_box)
        right_section.addLayout(female_section)
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
        self.model.change_nid(self._data.find_key(self.current), self.current.nid)
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
        dlg = TagDialog.create(self)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.tag_box.edit.clear()
            self.tag_box.edit.addItems(DB.tags.keys())
            self.tag_box.edit.setCurrentTexts(self.current.tags)
        else:
            pass

    # def access_stats(self):
    #     dlg = StatTypeDialog.create()
    #     result = dlg.exec_()
    #     if result == QDialog.Accepted:
    #         self.class_stat_widget.update_stats()
    #     else:
    #         pass

    def select_male_map_sprite(self):
        res, ok = ResourceEditor.get(self, "Map Sprites")
        if ok:
            nid = res.nid
            self.current.male_map_sprite_nid = nid
            pix = get_map_sprite_icon(self.current, num=0, gender=0)
            self.male_map_sprite_label.setPixmap(pix)
            self.window.update_list()

    def select_female_map_sprite(self):
        res, ok = ResourceEditor.get(self, "Map Sprites")
        if ok:
            nid = res.nid
            self.current.female_map_sprite_nid = nid
            pix = get_map_sprite_icon(self.current, num=0, gender=5)
            self.female_map_sprite_label.setPixmap(pix)
            self.window.update_list()

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.short_name_box.edit.setText(current.short_name)
        self.long_name_box.edit.setText(current.long_name)
        self.desc_box.edit.setText(current.desc)
        self.tier_box.edit.setValue(current.tier)
        self.max_level_box.edit.setValue(current.max_level)
        self.movement_box.edit.setValue(current.movement_group)
        if current.promotes_from:
            self.promotes_from_box.edit.setValue(current.promotes_from)
        else:
            self.promotes_from_box.edit.setValue("None")
        # Need to make copies because otherwise ResetSelection calls
        # self.tag_box.updated which resets the current.tags
        turns_into = current.turns_into[:]
        tags = current.tags[:]
        self.turns_into_box.edit.clear()
        self.turns_into_box.edit.addItems(DB.classes.keys())
        self.turns_into_box.edit.setCurrentTexts(turns_into)
        self.tag_box.edit.clear()
        self.tag_box.edit.addItems(DB.tags.keys())
        self.tag_box.edit.setCurrentTexts(tags)

        self.class_stat_widget.update_stats()
        self.class_stat_widget.set_new_obj(current)

        self.exp_mult_box.edit.setValue(current.exp_mult)
        self.opp_exp_mult_box.edit.setValue(current.opponent_exp_mult)

        self.class_skill_widget.set_current(current.learned_skills)
        self.wexp_gain_widget.set_current(current.wexp_gain)

        self.icon_edit.set_current(current.icon_nid, current.icon_index)
        pix = get_map_sprite_icon(self.current, num=0, gender=0)
        if pix:
            self.male_map_sprite_label.setPixmap(pix)
        else:
            self.male_map_sprite_label.clear()
        pix = get_map_sprite_icon(self.current, num=0, gender=5)
        if pix:
            self.female_map_sprite_label.setPixmap(pix)
        else:
            self.female_map_sprite_label.clear()

# Testing
# Run "python -m app.editor.class_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ClassDatabase.create()
    window.show()
    app.exec_()
