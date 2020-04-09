from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QDialog, QSplitter, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QTableView, QRadioButton, QStyledItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel

from app.data.weapons import WexpGainData
from app.data.skills import LearnedSkillList
from app.data.resources import RESOURCES
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, QHLine, DeletionDialog
from app.extensions.multi_select_combo_box import MultiSelectComboBox
from app.extensions.list_models import VirtualListModel
from app.extensions.list_widgets import BasicSingleListWidget, AppendMultiListWidget

from app.editor.custom_widgets import UnitBox, ClassBox
from app.editor.base_database_gui import DatabaseTab, DragDropCollectionModel
from app.editor.tag_widget import TagDialog
from app.editor.stat_widget import StatListWidget, StatAverageDialog, UnitStatAveragesModel
from app.editor.skill_database import LearnedSkillDelegate
from app.editor.item_database import ItemListWidget
import app.editor.weapon_database as weapon_database
from app.editor.icons import UnitPortrait
import app.editor.utilities as editor_utilities
from app import utilities
from app.editor.helper_funcs import can_wield

class UnitDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.units
        title = "Unit"
        right_frame = UnitProperties
        deletion_criteria = (None, None, None)
        collection_model = UnitModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

class WexpModel(VirtualListModel):
    def __init__(self, columns, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self._data: WexpGainData = data

    def rowCount(self, parent=None):
        return 1

    def columnCount(self, parent=None):
        return len(self._headers)

    def set_new_data(self, wexp_gain: WexpGainData):
        self._data: WexpGainData = wexp_gain
        self.layoutChanged.emit()

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            # return self._columns[idx].nid
            return None
        elif role == Qt.DecorationRole and orientation == Qt.Horizontal:
            weapon = self._columns[idx]
            pixmap = weapon_database.get_pixmap(weapon)
            if pixmap:
                return QIcon(pixmap)
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            weapon = self._columns[index.column()]
            wexp_gain = self._data.get(weapon.nid)
            if wexp_gain:
                return wexp_gain.wexp_gain
            else:
                return 0
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        weapon = self._columns[index.column()]
        wexp_gain = self._data.get(weapon.nid)
        wexp_gain.wexp_gain = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
        return basic_flags

class HorizWeaponListWidget(BasicSingleListWidget):
    def __init__(self, data, title, dlgate, parent=None):
        QWidget.__init__(self, parent)
        self.initiate(data, parent)

        self.model = WexpModel(DB.weapons, data, self)
        self.view = QTableView(self)
        self.view.setModel(self.model)
        delegate = dlgate(self.view)
        self.view.setItemDelegate(delegate)

        self.placement(data, title)

        for col in range(len(DB.weapons)):
            self.view.resizeColumnToContents(col)
            self.view.setColumnWidth(col, 20)

def get_chibi(unit):
    res = RESOURCES.portraits.get(unit.portrait_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(96, 16, 32, 32)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class UnitModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit = self._data[index.row()]
            text = unit.nid
            return text
        elif role == Qt.DecorationRole:
            unit = self._data[index.row()]
            # Get chibi image
            pixmap = get_chibi(unit)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        return None

    def delete(self, idx):
        # check to make sure nothing else is using me!!!
        unit = self._data[idx]
        nid = unit.nid
        affected_ais = [ai for ai in DB.ai if 
                        any(behaviour.target_spec and 
                        behaviour.target_spec[0] == "Unit" and 
                        behaviour.target_spec[1] == nid 
                        for behaviour in ai.behaviours)]
        if affected_ais:
            from app.editor.ai_database import AIModel
            model = AIModel
            msg = "Deleting Unit <b>%s</b> would affect these ais" % nid
            swap, ok = DeletionDialog.get_swap(affected_ais, model, msg, UnitBox(self.window, exclude=unit), self.window)
            if ok:
                self.change_nid(nid, swap.nid)
            else:
                return
        # Delete watchers
        for level in DB.levels:
            level.units = [unit for unit in level.units if nid != unit.nid]
        super().delete(idx)

    def change_nid(self, old_nid, new_nid):
        for ai in DB.ai:
            for behaviour in ai.behaviours:
                if behaviour.target_spec and behaviour.target_spec[0] == "Unit" and behaviour.target_spec[1] == old_nid:
                    behaviour.target_spec[1] = new_nid

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New Unit", nids)
        DB.create_new_unit(nid, name)

class GenderGroup(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.male = QRadioButton('M', self)
        self.male.toggled.connect(self.male_toggled)
        self.female = QRadioButton('F', self)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.male)
        layout.addWidget(self.female)

    def male_toggled(self, checked):
        self.toggled.emit(checked)

    def setValue(self, gender):
        if gender < 5:
            self.male.setChecked(True)
        else:
            self.female.setChecked(True)

class UnitProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self.view = self.window.left_frame.view
        self.model = self.window.left_frame.model
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = UnitPortrait(self)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)
        self.name_box.edit.setMaxLength(13)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        top_section.addLayout(name_section)

        main_section = QGridLayout()

        self.gender_box = PropertyBox("Gender", GenderGroup, self)
        self.gender_box.edit.toggled.connect(self.gender_changed)
        main_section.addWidget(self.gender_box, 0, 0)

        self.desc_box = PropertyBox("Description", QLineEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)
        main_section.addWidget(self.desc_box, 0, 1, 1, 3)

        self.level_box = PropertyBox("Level", QSpinBox, self)
        self.level_box.edit.setRange(1, 255)
        self.level_box.edit.setAlignment(Qt.AlignRight)
        self.level_box.edit.valueChanged.connect(self.level_changed)
        main_section.addWidget(self.level_box, 1, 0)

        self.class_box = ClassBox(self)
        self.class_box.edit.currentIndexChanged.connect(self.class_changed)
        main_section.addWidget(self.class_box, 1, 1)

        tag_section = QHBoxLayout()

        self.tag_box = PropertyBox("Personal Tags", MultiSelectComboBox, self)
        self.tag_box.edit.setPlaceholderText("No tag")
        self.tag_box.edit.addItems(DB.tags.keys())
        self.tag_box.edit.updated.connect(self.tags_changed)
        tag_section.addWidget(self.tag_box)

        self.tag_box.add_button(QPushButton('...'))
        self.tag_box.button.setMaximumWidth(40)
        self.tag_box.button.clicked.connect(self.access_tags)

        main_section.addLayout(tag_section, 1, 2, 1, 2)

        stat_section = QGridLayout()

        self.unit_stat_widget = StatListWidget(self.current, "Stats", reset_button=True, parent=self)
        self.unit_stat_widget.button.clicked.connect(self.display_averages)
        self.unit_stat_widget.reset_button.clicked.connect(self.reset_stats)
        self.unit_stat_widget.model.dataChanged.connect(self.stat_list_model_data_changed)
        self.averages_dialog = None
        # self.unit_stat_widget.button.clicked.connect(self.access_stats)
        # Changing of stats done automatically by using model view framework within
        stat_section.addWidget(self.unit_stat_widget, 1, 0, 1, 2)

        skill_section = QHBoxLayout()
        attrs = ("level", "skill_nid")
        self.personal_skill_widget = AppendMultiListWidget(LearnedSkillList(), "Personal Skills", attrs, LearnedSkillDelegate, self)
        # Changing of Personal skills done automatically also
        # self.personal_skill_widget.activated.connect(self.learned_skills_changed)
        skill_section.addWidget(self.personal_skill_widget)

        weapon_section = QHBoxLayout()
        attrs = ("weapon_type", "wexp_gain")
        self.wexp_gain_widget = HorizWeaponListWidget(WexpGainData.from_xml([], DB.weapons), "Starting Weapon Exp.", QStyledItemDelegate, self)
        # Changing of Weapon Gain done automatically
        # self.wexp_gain_widget.activated.connect(self.wexp_gain_changed)
        weapon_section.addWidget(self.wexp_gain_widget)

        item_section = QHBoxLayout()
        self.item_widget = ItemListWidget("Starting Items", self)
        self.item_widget.items_updated.connect(self.items_changed)
        item_section.addWidget(self.item_widget)

        total_section = QVBoxLayout()
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addWidget(QHLine())
        total_section.addLayout(stat_section)
        total_section.addLayout(weapon_section)
        total_widget = QWidget()
        total_widget.setLayout(total_section)

        right_section = QVBoxLayout()
        right_section.addLayout(item_section)
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

    def nid_changed(self, text):
        # Also change name if they are identical
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Unit ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self.model.change_nid(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text

    def gender_changed(self, male):
        if male:
            self.current.gender = 0
        else:
            self.current.gender = 5

    def desc_changed(self, text):
        self.current.desc = text

    def level_changed(self, val):
        self.current.level = val
        if self.averages_dialog:
            self.averages_dialog.update()

    def class_changed(self, index):
        self.current.klass = self.class_box.edit.currentText()
        self.level_box.edit.setMaximum(DB.classes.get(self.current.klass).max_level)
        if self.averages_dialog:
            self.averages_dialog.update()

    def tags_changed(self):
        self.current.tags = self.tag_box.edit.currentText()

    def reset_stats(self):
        model = self.unit_stat_widget.model
        view = self.unit_stat_widget.view
        selected_indexes = view.selectionModel().selectedIndexes()
        my_klass = DB.classes.get(self.current.klass)
        
        if not selected_indexes:
            # Select all
            topLeft = model.index(0, 0)
            bottomRight = model.index(model.rowCount() - 1, model.columnCount() - 1)
            selection = QItemSelection(topLeft, bottomRight)
            view.selectionModel().select(selection, QItemSelectionModel.Select)
            selected_indexes = view.selectionModel().selectedIndexes()

        for index in selected_indexes:
            stat_nid = DB.stats[index.column()].nid
            if index.row() == 0:
                class_value = my_klass.bases.get(stat_nid).value
            else:
                class_value = my_klass.growths.get(stat_nid).value
            model.setData(index, class_value, Qt.EditRole)

    def display_averages(self):
        # Modeless dialog
        if not self.averages_dialog:
            self.averages_dialog = StatAverageDialog(self.current, "Unit", UnitStatAveragesModel, self)
        self.averages_dialog.show()
        self.averages_dialog.raise_()
        self.averages_dialog.activateWindow()

    def close_averages(self):
        if self.averages_dialog:
            self.averages_dialog.done(0)
            self.averages_dialog = None

    def stat_list_model_data_changed(self, index1, index2):
        if self.averages_dialog:
            self.averages_dialog.update()

    # def learned_skills_changed(self):
    #     pass

    # def wexp_gain_changed(self):
    #     pass

    def items_changed(self):
        self.current.starting_items = self.item_widget.get_items()
        # See which ones can actually be wielded
        wieldable_list = []
        for item_nid, droppable in self.current.starting_items:
            item = DB.items.get(item_nid)
            wieldable_list.append(not can_wield(self.current, item, prefab=True))
        self.item_widget.set_color(wieldable_list)

    def access_tags(self):
        dlg = TagDialog.create(self)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            self.tag_box.edit.clear()
            self.tag_box.edit.addItems(DB.tags.keys())
            self.tag_box.edit.setCurrentTexts(self.current.tags)
        else:
            pass

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.gender_box.edit.setValue(current.gender)
        self.desc_box.edit.setText(current.desc)
        self.level_box.edit.setValue(current.level)
        self.class_box.edit.setValue(current.klass)
        tags = current.tags[:]
        self.tag_box.edit.clear()
        self.tag_box.edit.addItems(DB.tags.keys())
        self.tag_box.edit.setCurrentTexts(tags)

        self.unit_stat_widget.update_stats()
        self.unit_stat_widget.set_new_obj(current)
        if self.averages_dialog:
            self.averages_dialog.set_current(current)

        self.personal_skill_widget.set_current(current.learned_skills)
        self.wexp_gain_widget.set_current(current.wexp_gain)
        # print("Unit Set Current")
        # print(current.nid)
        # print(current.starting_items, flush=True)
        self.item_widget.set_current(current.starting_items)

        self.icon_edit.set_current(current.portrait_nid)

    def hideEvent(self, event):
        self.close_averages()

# Testing
# Run "python -m app.editor.unit_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = UnitDatabase.create()
    window.show()
    app.exec_()
