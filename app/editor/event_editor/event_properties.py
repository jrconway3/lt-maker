import math
from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, \
    QPlainTextEdit, QDialog, QPushButton, QListView, QStyledItemDelegate, QCheckBox, QAbstractItemView, \
    QGridLayout, QSizePolicy
from PyQt5.QtGui import QSyntaxHighlighter, QFont, QTextCharFormat, QColor, QTextCursor, QPainter, QPalette
from PyQt5.QtCore import QRegularExpression, Qt, QSettings, QSize, QRect

from app.extensions.custom_gui import PropertyBox, PropertyCheckBox, QHLine, ComboBox
from app.editor import timer

from app.resources.resources import RESOURCES
from app.data.database import DB
from app.utilities import str_utils
from app.editor.base_database_gui import CollectionModel
from app.events import event_prefab, event_commands, event_validators
from app.editor.event_editor import event_model
from app.editor import table_model
from app.editor.map_view import SimpleMapView
from app.extensions.custom_gui import TableView

@dataclass
class Rule():
    pattern: QRegularExpression
    _format: QTextCharFormat

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent, window):
        super().__init__(parent)
        self.window = window
        self.highlight_rules = []

        settings = QSettings('rainlash', 'Lex Talionis')
        theme = settings.value('theme', 0)
        if theme == 0:
            self.func_color = Qt.blue
            self.comment_color = Qt.darkGray
            self.bad_color = Qt.red
        else:
            self.func_color = QColor(102, 217, 239)
            self.comment_color = QColor(117, 113, 94)
            self.bad_color = QColor(249, 38, 114)

        function_head_format = QTextCharFormat()
        function_head_format.setForeground(self.func_color)
        function_head_format.setFontItalic(True)
        self.function_head_rule = Rule(
            QRegularExpression("^(.*?);"), function_head_format)
        self.highlight_rules.append(self.function_head_rule)

        comment_format = QTextCharFormat()
        comment_format.setForeground(self.comment_color)
        self.comment_rule = Rule(
            QRegularExpression("#[^\n]*"), comment_format)
        self.highlight_rules.append(self.comment_rule)

    def highlightBlock(self, text):
        for rule in self.highlight_rules:
            match_iterator = rule.pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule._format)

        lint_format = QTextCharFormat()
        lint_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        lint_format.setUnderlineColor(self.bad_color)
        lines = [l.strip() for l in text.splitlines()]
        # lines = [l.split('#', 1)[0] for l in lines]  # Remove comment character
        for line in lines:
            # Don't process comments
            line = line.split('#', 1)[0]
            if not line:
                continue
            broken_sections = self.validate_line(line)
            sections = line.split(';')
            running_length = 0
            for idx, section in enumerate(sections):
                if idx in broken_sections:
                    self.setFormat(running_length, len(section), lint_format)
                running_length += len(section) + 1

    def validate_line(self, line) -> list:
        try:
            command = event_commands.parse_text(line)
            if command:
                true_values, flags = event_commands.parse(command)
                broken_args = []
                for idx, value in enumerate(true_values):
                    if idx >= len(command.keywords):
                        i = idx - len(command.keywords)
                        if i < len(command.optional_keywords):
                            validator = command.optional_keywords[i]
                        elif value in flags:
                            continue
                        else:
                            broken_args.append(idx + 1)
                            continue
                    else:
                        validator = command.keywords[idx]
                    level_nid = self.window.current.level_nid
                    level = DB.levels.get(level_nid)
                    text = event_validators.validate(validator, value, level)
                    if text is None:
                        broken_args.append(idx + 1)
                return broken_args
            else:
                return [0]  # First arg is broken
        except:
            return []

class LineNumberArea(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.editor = parent

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.line_number_area = LineNumberArea(self)

        settings = QSettings('rainlash', 'Lex Talionis')
        theme = settings.value('theme', 0)
        if theme == 0:
            self.line_number_color = Qt.darkGray
        else:
            self.line_number_color = QColor(144, 144, 138)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.line_number_area.update)

        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        bg_color = self.palette().color(QPalette.Base)
        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while (block.isValid() and top <= event.rect().bottom()):
            if (block.isVisible() and bottom >= event.rect().top()):
                number = str(block_number + 1)
                if self.textCursor().blockNumber() == block_number:
                    color = self.palette().color(QPalette.Window)
                    painter.fillRect(0, top, self.line_number_area.width(), self.fontMetrics().height(), color)
                painter.setPen(self.line_number_color)
                painter.drawText(0, top, self.line_number_area.width() - 2, self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def lineNumberAreaWidth(self) -> int:
        num_blocks = max(1, self.blockCount())
        digits = math.ceil(math.log(num_blocks, 10))
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits

        return space

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self, newBlockCount: int):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

class EventCollection(QWidget):
    def __init__(self, deletion_criteria, collection_model, parent,
                 button_text="Create %s", view_type=TableView):
        super().__init__(parent)
        self.window = parent

        self._data = self.window._data
        self.title = self.window.title

        self.display = None
        grid = QGridLayout()
        self.setLayout(grid)

        self.model = collection_model(self._data, self)
        self.proxy_model = table_model.ProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.view = view_type(None, self)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setModel(self.proxy_model)
        # self.view.setModel(self.model)
        self.view.setSortingEnabled(True)
        # self.view.clicked.connect(self.on_single_click)
        # Remove edit on double click
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.view.currentChanged = self.on_item_changed
        self.view.selectionModel().selectionChanged.connect(self.on_item_changed)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.button = QPushButton(button_text % self.title)
        self.button.clicked.connect(self.model.append)

        grid.addWidget(self.view, 0, 0)
        grid.addWidget(self.button, 1, 0)

    def on_item_changed(self, curr, prev):
        if self._data:
            if curr.indexes():
                index = curr.indexes()[0]
                correct_index = self.proxy_model.mapToSource(index)
                row = correct_index.row()
            else:
                return
            # new_data = curr.internalPointer()  # Internal pointer is way too powerful
            # if not new_data:
            new_data = self._data[row]
            if self.display:
                self.display.set_current(new_data)
                self.display.setEnabled(True)

    def set_display(self, disp):
        self.display = disp
        first_index = self.model.index(0, 0)
        self.view.setCurrentIndex(first_index)

    def update_list(self):
        # self.model.layoutChanged.emit()
        self.proxy_model.invalidateFilter()

class EventProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        self.text_box = CodeEditor(self)
        self.text_box.textChanged.connect(self.text_changed)

        # Text setup
        self.cursor = self.text_box.textCursor()
        self.font = QFont()
        self.font.setFamily("Courier")
        self.font.setFixedPitch(True)
        self.font.setPointSize(10)
        self.text_box.setFont(self.font)
        self.highlighter = Highlighter(self.text_box.document(), self)

        main_section = QVBoxLayout()
        self.setLayout(main_section)
        main_section.addWidget(self.text_box)

        left_frame = self.window.left_frame
        grid = left_frame.layout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)

        self.trigger_box = PropertyBox("Trigger", ComboBox, self)
        items = self.get_trigger_items("Global")
        self.trigger_box.edit.addItems(items)
        self.trigger_box.edit.activated.connect(self.trigger_changed)

        self.level_nid_box = PropertyBox("Level", ComboBox, self)
        self.level_nid_box.edit.addItem("Global")
        self.level_nid_box.edit.addItems(DB.levels.keys())
        self.level_nid_box.edit.currentIndexChanged.connect(self.level_nid_changed)

        self.condition_box = PropertyBox("Condition", QLineEdit, self)
        self.condition_box.edit.setPlaceholderText("Condition required for event to fire")
        self.condition_box.edit.textChanged.connect(self.condition_changed)

        self.only_once_box = PropertyCheckBox("Trigger only once?", QCheckBox, self)
        self.only_once_box.edit.stateChanged.connect(self.only_once_changed)
        
        grid.addWidget(QHLine(), 2, 0)
        grid.addWidget(self.nid_box, 3, 0)
        grid.addWidget(self.level_nid_box, 4, 0)
        grid.addWidget(self.trigger_box, 5, 0)
        grid.addWidget(self.condition_box, 6, 0)
        grid.addWidget(self.only_once_box, 7, 0, Qt.AlignLeft)

        bottom_section = QHBoxLayout()
        main_section.addLayout(bottom_section)

        self.show_map_dialog = None
        self.show_map_button = QPushButton("Show Map")
        self.show_map_button.clicked.connect(self.show_map)
        bottom_section.addWidget(self.show_map_button)
        self.show_map_button.setEnabled(False)

        self.show_commands_dialog = None
        # self.show_commands_button = QPushButton("Show Commands")
        # self.show_commands_button.clicked.connect(self.show_commands)
        # bottom_section.addWidget(self.show_commands_button)

    def get_trigger_items(self, level_nid: str) -> list:
        all_items = ["None"]
        all_custom_triggers = set()
        for level in DB.levels:
            if level_nid == 'Global' or level_nid == level.nid: 
                for region in level.regions:
                    if region.region_type == 'Event':
                        all_custom_triggers.add(region.sub_nid)
        all_items += list(all_custom_triggers)
        all_items += [trigger.nid for trigger in event_prefab.all_triggers]
        return all_items

    def insert_text(self, text):
        self.text_box.insertPlainText(text)

    def insert_text_with_newline(self, text):
        self.cursor.movePosition(QTextCursor.NextBlock)
        self.text_box.insertPlainText(text)

    def show_map(self):
        # Modeless dialog
        if not self.show_map_dialog:
            current_level = DB.levels.get(self.current.level_nid)
            self.show_map_dialog = ShowMapDialog(current_level, self)
        self.show_map_dialog.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.show_map_dialog.setWindowFlags(self.show_map_dialog.windowFlags() | Qt.WindowDoesNotAcceptFocus)
        self.show_map_dialog.show()
        self.show_map_dialog.raise_()
        # self.show_map_dialog.activateWindow()

    def close_map(self):
        if self.show_map_dialog:
            self.show_map_dialog.done(0)
            self.show_map_dialog = None

    # def show_commands(self):
    #     # Modeless dialog
    #     if not self.show_commands_dialog:
    #         self.show_commands_dialog = ShowCommandsDialog(self)
    #     self.show_commands_dialog.setAttribute(Qt.WA_ShowWithoutActivating, True)
    #     self.show_commands_dialog.setWindowFlags(self.show_commands_dialog.windowFlags() | Qt.WindowDoesNotAcceptFocus)
    #     self.show_commands_dialog.show()
    #     self.show_commands_dialog.raise_()
    #     # self.show_commands_dialog.activateWindow()

    # def close_commands(self):
    #     if self.show_commands_dialog:
    #         self.show_commands_dialog.done(0)
    #         self.show_commands_dialog = None

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Event ID %s already in use' % self.current.nid)
            self.current.nid = str_utils.get_next_name(self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def trigger_changed(self, idx):
        cur_val = self.trigger_box.edit.currentText()
        if cur_val == 'None':
            self.current.trigger = None
        elif cur_val in [trigger.nid for trigger in event_prefab.all_triggers]:
            self.current.trigger = cur_val
        else:
            self.current.trigger = cur_val

    def level_nid_changed(self, idx):
        print("Level Nid Change")
        print(idx)
        if idx == 0:
            self.current.level_nid = None
            self.show_map_button.setEnabled(False)
        else:
            self.current.level_nid = DB.levels[idx - 1].nid
            current_level = DB.levels.get(self.current.level_nid)
            if current_level.tilemap:
                self.show_map_button.setEnabled(True)
            else:
                self.show_map_button.setEnabled(False)

        # Update trigger box to match current level
        self.trigger_box.edit.clear()
        print(self.trigger_box.edit.count())
        if idx == 0:
            self.trigger_box.edit.addItems(self.get_trigger_items("Global"))
        else:
            self.trigger_box.edit.addItems(self.get_trigger_items(self.current.level_nid))

    def condition_changed(self, text):
        self.current.condition = text

    def only_once_changed(self, state):
        self.current.only_once = bool(state)

    def text_changed(self):
        self.current.commands.clear()
        text = self.text_box.toPlainText()
        lines = [l.strip() for l in text.splitlines()]
        for line in lines:
            command = event_commands.parse_text(line)
            if command:
                self.current.commands.append(command)

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        # self.trigger_box.edit.clear()
        if current.level_nid:
            self.level_nid_box.edit.setValue(current.level_nid)
            # self.trigger_box.edit.addItems(self.get_trigger_items(current.level_nid))
        else:
            self.level_nid_box.edit.setValue('Global')
            # self.trigger_box.edit.addItems(self.get_trigger_items("Global"))
        self.trigger_box.edit.setValue(current.trigger)
        self.condition_box.edit.setText(current.condition)
        self.only_once_box.edit.setChecked(bool(current.only_once))

        # Convert text
        text = ''
        for command in current.commands:
            text += command.to_plain_text()
            text += '\n'

        self.text_box.setPlainText(text)
    
    def hideEvent(self, event):
        self.close_map()
        # self.close_commands()

class ShowMapDialog(QDialog):
    def __init__(self, current_level, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle("Level Map View")
        self.window = parent
        self.current_level = current_level

        self.map_view = SimpleMapView(self)
        self.map_view.position_clicked.connect(self.position_clicked)
        self.map_view.position_moved.connect(self.position_moved)
        self.map_view.set_current_level(self.current_level)
        tilemap = RESOURCES.tilemaps.get(self.current_level.tilemap)
        if tilemap:
            self.map_view.set_current_map(tilemap)

        self.position_edit = QLineEdit(self)
        self.position_edit.setAlignment(Qt.AlignRight)
        self.position_edit.setReadOnly(True)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.map_view)
        layout.addWidget(self.position_edit, Qt.AlignRight)

        timer.get_timer().tick_elapsed.connect(self.map_view.update_view)

    def position_clicked(self, x, y):
        self.window.insert_text("%d,%d" % (x, y))

    def position_moved(self, x, y):
        if x >= 0 and y >= 0:
            self.position_edit.setText("%d,%d" % (x, y))
        else:
            self.position_edit.setText("")

    def update(self):
        self.map_view.update_view()

    def set_current(self, current):
        self.current_level = current
        self.map_view.set_current_level(self.current_level)
        tilemap = RESOURCES.tilemaps.get(self.current_level.tilemap)
        if tilemap:
            self.map_view.set_current_map(tilemap)

    def closeEvent(self, event):
        self.window.show_map_dialog = None

class ShowCommandsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle("Event Commands")
        self.window = parent

        self._data = event_commands.get_commands()
        self.model = EventCommandModel(self._data, self)
        self.view = QListView(self)
        self.view.setMinimumSize(128, 360)
        self.view.setModel(self.model)
        self.view.doubleClicked.connect(self.on_double_click)

        self.delegate = CommandDelegate(self._data, self)
        self.view.setItemDelegate(self.delegate)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.view)

    def on_double_click(self, index):
        idx = index.row()
        command = self._data[idx]
        self.window.insert_text_on_newline(command.nid)

class EventCommandModel(CollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            command = self._data[index.row()]
            text = command.nid
            return text

class CommandDelegate(QStyledItemDelegate):
    def __init__(self, data, parent=None):
        super().__init__(parent=None)
        self._data = data

    def sizeHint(self, option, index):
        return QSize(0, 48)

    def paint(self, painter, option, index):
        command = self._data[index.row()]
        rect = option.rect
        left = rect.left()
        right = rect.right()
        top = rect.top()
        bottom = rect.bottom()
        font = painter.font()
        font_height = 16
        if command.nickname:
            painter.drawText(left, top, "%s (%s)" % (command.nid, command.nickname))
        else:
            painter.drawText(left, top, command.nid)
        painter.drawLine(left, top + font_height, right, top + font_height)
        keywords = ";".join(command.keywords)
        optional_keywords = ";".join(command.optional_keywords)
        flags = ";".join(command.flags)
        painter.drawText(left, top + font_height + 4, keywords)
        # italics
        font.setItalic(True)
        painter.drawText(left, top + font_height*2 + 4, optional_keywords)
        painter.drawText(left, top + font_height*3 + 4, "{" + flags + "}")
