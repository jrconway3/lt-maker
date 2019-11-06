from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, \
    QMessageBox, QSpinBox, QHBoxLayout, QPushButton, QDialog, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QTreeView, QDoubleSpinBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.stats import StatList
from app.data.database import DB

from app.editor.custom_gui import PropertyBox, ComboBox, QHLine, IntDelegate, VirtualListModel
from app.editor.multi_select_combo_box import MultiSelectComboBox
from app.editor.base_database_gui import DatabaseDialog, CollectionModel
from app.editor.misc_dialogs import TagDialog, StatDialog
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
    def __init__(self, klass, parent=None):
        super().__init__(parent)
        self.window = parent
        self._klass = klass

        column_titles = DB.stats.keys()
        row_titles = ['Generic Bases', 'Generic Growths', 'Promotion Gains', 'Growth Bonuses', 'Stat Maximums']
        if klass:
            row_values = klass.get_stat_lists()
        else:
            row_values = [StatList([], DB.stats)] * 5

        self.model = StatModel(column_titles, row_titles, row_values, self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        delegate = IntDelegate(self.view, range(len(column_titles)))
        self.view.setItemDelegate(delegate)
        for col in range(len(column_titles)):
            self.view.resizeColumnToContents(col)

        layout = QHBoxLayout(self)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def set_new_klass(self, klass):
        self._klass = klass
        row_values = klass.get_stat_lists()
        self.model.set_new_data(row_values)

    def update_stats(self):
        column_titles = DB.stats.keys()
        self.model.update_column_header(column_titles)
        self.set_new_klass(self._klass)

class StatModel(VirtualListModel):
    def __init__(self, columns, rows, data, parent=None):
        super().__init__(parent)
        self.window = parent
        self._columns = self._headers = columns
        self._rows = rows
        self._data = data  # Must be StatList

    def set_new_data(self, row_values):
        self._data = row_values
        self.layoutChanged.emit()

    def update_column_header(self, columns):
        self._columns = self._headers = columns

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return self._rows[idx]
        elif orientation == Qt.Horizontal:
            return self._columns[idx]

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            row = self._data[index.row()]
            key = self._columns[index.column()]
            return row[key]
        elif role == Qt.EditRole:
            row = self._data[index.row()]
            key = self._columns[index.column()]
            return row[key]
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight + Qt.AlignVCenter

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        row = self._data[index.row()]
        key = self._columns[index.column()]
        row[key] = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        basic_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
        return basic_flags

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
        main_section.addWidget(self.desc_box, 0, 0, 1, 4)

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
        stat_label = QLabel("Stats")
        stat_label.setAlignment(Qt.AlignBottom)
        stat_section.addWidget(stat_label, 0, 0, Qt.AlignBottom)

        self.access_stat_button = QPushButton("...")
        self.access_stat_button.setMaximumWidth(40)
        self.access_stat_button.clicked.connect(self.access_stats)
        stat_section.addWidget(self.access_stat_button, 0, 1)

        self.class_stat_widget = ClassStatWidget(self.current, self)
        stat_section.addWidget(self.class_stat_widget, 1, 0, 1, 2)

        weapon_section = QHBoxLayout()

        skill_section = QHBoxLayout()

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
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        total_section.addLayout(tag_section)
        h_line = QHLine()
        total_section.addWidget(h_line)
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
            self.update_stats()
        else:
            pass

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
        self.turns_into_box.edit.ResetSelection()
        self.turns_into_box.edit.setCurrentTexts(current.turns_into)
        self.tag_box.edit.ResetSelection()
        self.tag_box.edit.setCurrentTexts(current.tags)

        self.class_stat_widget.set_new_klass(current)

        self.exp_mult_box.edit.setValue(self.current.exp_mult)
        self.opp_exp_mult_box.edit.setValue(self.current.opponent_exp_mult)

# Testing
# Run "python -m app.editor.class_database" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ClassDatabase.create()
    window.show()
    app.exec_()
