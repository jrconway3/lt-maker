from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QDialog, QSplitter, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QTableView, QRadioButton, QStyledItemDelegate
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from app.data.weapons import WexpGainList
from app.data.skills import LearnedSkillList
from app.data.database import DB

from app.editor.custom_gui import PropertyBox, ComboBox, QHLine, VirtualListModel
from app.editor.multi_select_combo_box import MultiSelectComboBox
from app.editor.base_database_gui import DatabaseTab, CollectionModel
from app.editor.misc_dialogs import TagDialog, StatDialog
from app.editor.sub_list_widget import BasicSingleListWidget, AppendMultiListWidget
from app.editor.stat_widget import UnitStatWidget
from app.editor.skill_database import LearnedSkillDelegate
from app.editor.item_database import ItemListWidget
from app.editor.icons import UnitPortrait
from app import utilities

class UnitDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = DB.units
        title = "Unit"
        right_frame = UnitProperties
        deletion_criteria = None
        collection_model = UnitModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = utilities.get_next_name("New " + self.title, nids)
        DB.create_new_unit(nid, name)
        self.after_new()

class WexpModel(VirtualListModel):
    def __init__(self, columns, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self._data: WexpGainList = data

    def rowCount(self, parent=None):
        return 1

    def columnCount(self, parent=None):
        return len(self._headers)

    def set_new_data(self, wexp_gain_list: WexpGainList):
        self._data: WexpGainList = wexp_gain_list
        self.layoutChanged.emit()

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            # return self._columns[idx].nid
            return None
        elif role == Qt.DecorationRole and orientation == Qt.Horizontal:
            weapon = self._columns[idx]
            x, y = weapon.icon_index
            pixmap = QPixmap(weapon.icon_fn).copy(x*16, y*16, 16, 16)
            return QIcon(pixmap)
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            wexp_gain = self._data[index.column()]
            return wexp_gain.wexp_gain
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        wexp_gain = self._data[index.column()]
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
        for col in range(len(DB.weapons)):
            self.view.resizeColumnToContents(col)

        self.placement(data, title)

class UnitModel(CollectionModel):
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
            pixmap = QPixmap(unit.portrait_fn).copy(96, 16, 32, 32)
            if pixmap.width() > 0 and pixmap.height > 0:
                return QIcon(pixmap)
            else:
                return None
        return None

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
        self._data = self.window._data
        self.database_editor = self.window.window

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = UnitPortrait(None, self)
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

        self.class_box = PropertyBox("Class", ComboBox, self)
        self.class_box.edit.addItems(DB.classes.keys())
        self.class_box.edit.currentIndexChanged.connect(self.class_changed)
        main_section.addWidget(self.class_box, 1, 1)

        tag_section = QHBoxLayout()

        self.tag_box = PropertyBox("Personal Tags", MultiSelectComboBox, self)
        self.tag_box.edit.setPlaceholderText("No tag")
        self.tag_box.edit.addItems(DB.tags)
        self.tag_box.edit.updated.connect(self.tags_changed)
        tag_section.addWidget(self.tag_box)

        self.tag_box.add_button(QPushButton('...'))
        self.tag_box.button.setMaximumWidth(40)
        self.tag_box.button.clicked.connect(self.access_tags)

        main_section.addLayout(tag_section, 1, 3, 1, 2)

        stat_section = QGridLayout()

        self.unit_stat_widget = UnitStatWidget(self.current, "Stats", self)
        self.unit_stat_widget.button.clicked.connect(self.access_stats)
        stat_section.addWidget(self.unit_stat_widget, 1, 0, 1, 2)

        skill_section = QHBoxLayout()
        attrs = ("level", "skill_nid")
        self.personal_skill_widget = AppendMultiListWidget(LearnedSkillList(), "Personal Skills", attrs, LearnedSkillDelegate, self)
        skill_section.addWidget(self.personal_skill_widget)

        weapon_section = QHBoxLayout()
        attrs = ("weapon_type", "wexp_gain")
        self.wexp_gain_widget = HorizWeaponListWidget(WexpGainList([], DB.weapons), "Starting Weapon Exp.", QStyledItemDelegate, self)
        weapon_section.addWidget(self.wexp_gain_widget)

        item_section = QHBoxLayout()
        self.item_widget = ItemListWidget("Starting Items", self)
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
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Unit ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text

    def gender_changed(self, male):
        if male:
            self.gender = 0
        else:
            self.gender = 5

    def desc_changed(self, text):
        self.current.desc = text

    def level_changed(self, val):
        self.current.max_level = val

    def class_changed(self, index):
        self.current.klass = self.class_box.edit.currentText()
        self.level_box.edit.setMaximum(DB.classes.get(self.current.klass).max_level)

    def tags_changed(self):
        self.current.tags = self.tag_box.edit.currentText()

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
            self.unit_stat_widget.update_stats()
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
        self.tag_box.edit.ResetSelection()
        self.tag_box.edit.setCurrentTexts(current.tags)

        self.unit_stat_widget.set_new_obj(current)

        self.personal_skill_widget.set_current(self.current.learned_skills)
        self.wexp_gain_widget.set_current(self.current.wexp_gain)
        self.item_widget.set_current(self.current.items)

# Testing
# Run "python -m app.editor.unit_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = UnitDatabase.create()
    window.show()
    app.exec_()
