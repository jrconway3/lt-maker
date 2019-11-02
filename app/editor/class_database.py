from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QTreeView
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.database import DB

from app.editor.custom_gui import PropertyBox, ComboBox, IntDelegate, MultiAttrListModel
from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app.editor.icons import ItemIcon80
from app import utilities

class ClassDatabase(DatabaseDialog):
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

class ClassStatWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data

        column_titles = [''] + DB.stats.keys()
        self.model = MultiAttrListModel(self._data, column_titles, column_titles, self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        delegate = IntDelegate(self.view, range(len(column_titles)))
        self.view.setItemDelegate(delegate)
        for col in range(len(column_titles)):
            self.view.resizeColumnToContents(col)

        layout = QHBoxLayout(self)
        layout.addWidget(self.view)
        self.setLayout(layout)

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

        self.setStyleSheet("fond: 10pt;")

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

        self.short_name_box = PropertyBox("Shortened Display Name", QLineEdit, self)
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
        main_section.addWidget(self.desc_box, 0, 0, 1, 6)

        self.tier_box = PropertyBox("Tier", QSpinBox, self)
        self.tier_box.edit.setRange(0, 5)
        self.tier_box.edit.valueChanged.connect(self.tier_changed)
        main_section.addWidget(self.tier_box, 1, 0, 1, 2)

        self.promotes_from_box = PropertyBox("Promotes From", ComboBox, self)
        self.promotes_from_box.addItems(["None"] + DB.classes.keys())
        self.promotes_from_box.edit.currentIndexChanged.connect(self.promotes_from_changed)
        main_section.addWidget(self.promotes_from_box, 1, 3, 1, 2)

        self.max_level_box = PropertyBox("Max Level", QSpinBox, self)
        self.max_level_box.setRange(1, 255)
        self.max_level_box.edit.valueChanged.connect(self.max_level_changed)
        main_section.addWidget(self.max_level_box, 1, 5, 1, 2)

        self.turns_into_box = PropertyBox("Turns Into", MultiComboBox, self)
        self.turns_into_box.addItems(DB.classes.keys())
        self.turns_into_box.edit.currentChanged.connect(self.turns_into_changed)
        main_section.addWidget(self.turns_into_box, 2, 0, 1, 3)

        self.tag_box = PropertyBox("Tags", MultiComboBox, self)
        self.tag_box.addItems(DB.tags)
        self.tag_box.edit.currentChanged.connect(self.tags_changed)
        main_section.addWidget(self.tag_box, 2, 4, 1, 3)

        self.tag_box.add_button(QPushButton('...'))
        self.tag_box.button.setMaximumWidth(40)
        self.tag_box.button.clicked.connect(self.access_tags)

        stat_section = QGridLayout()
        stat_label = QLabel("Stats")
        stat_label.setAlignment(Qt.AlignBottom)
        stat_section.addWidget(stat_label, 0, 0, Qt.AlignBottom)

        self.access_stat_button = QPushButton("...")
        self.access_stat_button.clicked.connect(self.access_stats)
        stat_section.addWidget(self.access_stat_button, 0, 1)

        self.class_stat_widget = ClassStatWidget(self)
        stat_section.addWidget(self.class_stat_widget, 1, 0, 1, 2)

        weapon_section = QHBoxLayout()

        skill_section = QHBoxLayout()

        exp_section = QHBoxLayout()

        self.exp_mult_box = PropertyBox("Exp Multiplier", QLineEdit, self)
        # TODO add Double Validator (0 - 255?)
        self.exp_mult_box.edit.textChanged.connect(self.exp_mult_changed)
        exp_section.addWidget(self.exp_mult_box)

        self.opp_exp_mult_box = PropertyBox("Opponent Exp Multiplier", QLineEdit, self)
        # TODO add Double Validator (0 - 255?)
        self.opp_exp_mult_box.edit.textChanged.connect(self.opp_exp_mult_changed)
        exp_section.addWidget(self.opp_exp_mult_box)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addLayout(stat_section)
        total_section.addLayout(weapon_section)
        total_section.addLayout(skill_section)
        total_section.addLayout(exp_section)

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

    def max_level_changed(self, val):
        self.current.max_level = val

    def turns_into_changed(self):
        self.current.turns_into = self.turns_into_box.edit.currentSelections()

    def tags_changed(self):
        self.current.tags = self.tag_box.edit.currentSelections()

    def exp_mult_changed(self):
        self.current.exp_mult = float(self.exp_mult_box.edit.currentText())

    def opp_exp_mult_changed(self):
        self.current.opponent_exp_mult = float(self.opp_exp_mult_box.edit.currentText)

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.short_name_box.edit.setText(current.short_name)
        self.long_name_box.edit.setText(current.long_name)
        self.desc_box.edit.setText(current.desc)
        self.tier_box.edit.setValue(current.tier)
        self.max_level_box.edit.setValue(current.max_level)
        if current.promotes_from:
            self.promotes_from_box.edit.setValue(current.promotes_from)
        else:
            self.promotes_from_box.edit.setValue("None")
        self.turns_into_box.edit.setValue(current.turns_into)
        self.tag_box.edit.setValue(current.tags)

        self.exp_mult_box.edit.setText(self.current.exp_mult)
        self.opp_exp_mult_box.edit.setText(self.current.opponent_exp_mult)

# Testing
# Run "python -m app.editor.class_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ClassDatabase.create()
    window.show()
    app.exec_()
