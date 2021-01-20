import math
from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, \
    QPlainTextEdit, QDialog, QPushButton, QListView, QStyledItemDelegate, QCheckBox, QAbstractItemView, \
    QGridLayout, QSizePolicy, QAction
from PyQt5.QtGui import QSyntaxHighlighter, QFont, QTextCharFormat, QColor, QTextCursor, QPainter, QPalette, QFontMetrics
from PyQt5.QtCore import QRegularExpression, Qt, QSize, QRect

from app.extensions.custom_gui import PropertyBox, PropertyCheckBox, QHLine, ComboBox
from app.editor import timer
from app.editor.settings import MainSettingsController

from app.resources.resources import RESOURCES
from app.data.database import DB
from app.utilities import str_utils
from app.editor.base_database_gui import CollectionModel
from app.events import event_prefab, event_commands, event_validators
from app.editor.event_editor import find_and_replace
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

        settings = MainSettingsController()
        theme = settings.get_theme()
        if theme == 0:
            self.func_color = QColor(52, 103, 174)
            self.comment_color = Qt.darkGray
            self.bad_color = Qt.red
            self.text_color = QColor(63, 109, 58)
            self.special_text_color = Qt.darkMagenta
            self.special_func_color = Qt.red
        else:
            self.func_color = QColor(102, 217, 239)
            self.comment_color = QColor(117, 113, 94)
            self.bad_color = QColor(249, 38, 114)
            self.text_color = QColor(230, 219, 116)
            self.special_text_color = QColor(174, 129, 255)
            self.special_func_color = (249, 38, 114)

        function_head_format = QTextCharFormat()
        function_head_format.setForeground(self.func_color)
        # First part of line with semicolon
        self.function_head_rule1 = Rule(
            QRegularExpression("^(.*?);"), function_head_format)
        # Any line without a semicolon
        self.function_head_rule2 = Rule(
            QRegularExpression("^[^;]+$"), function_head_format)
        self.highlight_rules.append(self.function_head_rule1)
        self.highlight_rules.append(self.function_head_rule2)

        self.text_format = QTextCharFormat()
        self.text_format.setForeground(self.text_color)
        self.special_text_format = QTextCharFormat()
        self.special_text_format.setForeground(self.special_text_color)

        comment_format = QTextCharFormat()
        comment_format.setForeground(self.comment_color)
        comment_format.setFontItalic(True)
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
        lines = text.splitlines()

        for line in lines:
            # Don't consider tabs when formatting
            num_tabs = 0
            while line.startswith('    '):
                line = line[4:]
                num_tabs += 1
            # Don't process comments
            line = line.split('#', 1)[0]
            if not line:
                continue
            broken_sections = self.validate_line(line)
            if broken_sections == 'all':
                self.setFormat(num_tabs * 4, len(line), lint_format)
            else:
                sections = line.split(';')
                running_length = num_tabs * 4
                for idx, section in enumerate(sections):
                    if idx in broken_sections:
                        self.setFormat(running_length, len(section), lint_format)
                    running_length += len(section) + 1

        # Extra formatting
        for line in lines:
            # Don't consider tabs
            num_tabs = 0
            while line.startswith('    '):
                line = line[4:]
                num_tabs += 1

            line = line.split('#', 1)[0]
            if not line:
                continue
            sections = line.split(';')
            # Handle text format
            if sections[0] in ('s', 'speak') and len(sections) >= 3:
                start = num_tabs * 4 + len(';'.join(sections[:2])) + 1
                self.setFormat(start, len(sections[2]), self.text_format)
                # Handle special text format
                special_start = 0
                for idx, char in enumerate(sections[2]):
                    if char == '|':
                        self.setFormat(start + idx, 1, self.special_text_format)
                    elif char == '{':
                        special_start = start + idx
                    elif char == '}':
                        self.setFormat(special_start, start + idx - special_start + 1, self.special_text_format)

    def validate_line(self, line) -> list:
        try:
            command = event_commands.parse_text(line)
            if command:
                true_values, flags = event_commands.parse(command)
                broken_args = []
                if len(command.keywords) > len(true_values):
                    return 'all'
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
        except Exception as e:
            return 'all'

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

        settings = MainSettingsController()
        theme = settings.get_theme()
        if theme == 0:
            self.line_number_color = Qt.darkGray
        else:
            self.line_number_color = QColor(144, 144, 138)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.line_number_area.update)

        self.updateLineNumberAreaWidth(0)
        # Set tab to four spaces
        fm = QFontMetrics(self.font())
        self.setTabStopWidth(4 * fm.width(' '))

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

    def keyPressEvent(self, event):
        # Shift + Tab is not the same as catching a shift modifier + tab key
        # Shift + Tab is a Backtab
        if event.key() == Qt.Key_Tab:
            cur = self.textCursor()
            cur.insertText("    ")
        elif event.key() == Qt.Key_Backtab:
            cur = self.textCursor()
            # Copy the current selection
            pos = cur.position()  # Where a selection ends
            anchor = cur.anchor()  # Where a selection starts (can be the same as above)
            cur.setPosition(pos)
            # Move the position back one, selecting the character prior to the original position
            cur.setPosition(pos - 1, QTextCursor.KeepAnchor)

            if str(cur.selectedText()) == "\t":
                # The prior character is a tab, so delete the selection
                cur.removeSelectedText()
                # Reposition the cursor
                cur.setPosition(anchor - 1)
                cur.setPosition(pos - 1, QTextCursor.KeepAnchor)
            elif str(cur.selectedText()) == " ":
                # Remove up to four spaces
                counter = 0
                while counter < 4 and all(c == " " for c in str(cur.selectedText())):
                    counter += 1
                    cur.setPosition(pos - 1 - counter, QTextCursor.KeepAnchor)
                cur.setPosition(pos - counter, QTextCursor.KeepAnchor)
                cur.removeSelectedText()
                # Reposition the cursor
                cur.setPosition(anchor)
                cur.setPosition(pos, QTextCursor.KeepAnchor)
            else:
                # Try all of the above, looking before the anchor
                cur.setPosition(anchor)
                cur.setPosition(anchor - 1, QTextCursor.KeepAnchor)
                if str(cur.selectedText()) == "\t":
                    cur.removeSelectedText()
                    cur.setPosition(anchor - 1)
                    cur.setPosition(pos - 1, QTextCursor.KeepAnchor)
                else:
                    # It's not a tab, so reset the selection to what it was
                    cur.setPosition(anchor)
                    cur.setPosition(pos, QTextCursor.KeepAnchor)
        else:
            return super().keyPressEvent(event)

class EventCollection(QWidget):
    def __init__(self, deletion_criteria, collection_model, parent,
                 button_text="Create %s", view_type=TableView):
        super().__init__(parent)
        self.window = parent
        self.database_editor = self.window.window
        self.main_editor = self.database_editor.window
        current_level_nid = self.main_editor.app_state_manager.state.selected_level
        self.current_level = DB.levels.get(current_level_nid)

        self._data = self.window._data
        self.title = self.window.title

        self.display = None
        grid = QGridLayout()
        self.setLayout(grid)

        self.level_filter_box = PropertyBox("Level Filter", ComboBox, self)
        self.level_filter_box.edit.addItem("All")
        self.level_filter_box.edit.addItem("Global")
        self.level_filter_box.edit.addItems(DB.levels.keys())
        self.level_filter_box.edit.currentIndexChanged.connect(self.level_filter_changed)

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
        self.button.clicked.connect(self.create_new_event)

        grid.addWidget(self.level_filter_box, 0, 0, Qt.AlignRight)
        grid.addWidget(self.view, 1, 0)
        grid.addWidget(self.button, 2, 0)

        if self.current_level:
            self.level_filter_box.edit.setValue(self.current_level.nid)
        else:
            self.level_filter_box.edit.setValue("All")

    def create_new_event(self):
        last_index = self.model.append()
        if last_index:
            last_event = DB.events[-1]
            if self.level_filter_box.edit.currentText() != "All":
                if last_event.level_nid:
                    self.level_filter_box.edit.setValue(last_event.level_nid)
                else:
                    self.level_filter_box.edit.setValue("Global")
            proxy_last_index = self.proxy_model.mapFromSource(last_index)
            self.view.setCurrentIndex(proxy_last_index)

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

    def set_current_index(self, index):
        correct_index = self.proxy_model.mapToSource(index)
        row = correct_index.row()
        new_data = self._data[row]
        if self.display:
            self.display.set_current(new_data)
            self.display.setEnabled(True)

    def set_display(self, disp):
        self.display = disp
        first_index = self.proxy_model.index(0, 0)
        self.view.setCurrentIndex(first_index)

    def level_filter_changed(self, idx):
        filt = self.level_filter_box.edit.currentText()
        self.view.selectionModel().selectionChanged.disconnect(self.on_item_changed)
        self.proxy_model.setFilterKeyColumn(1)
        if filt == 'All':
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterFixedString(filt)
        self.view.selectionModel().selectionChanged.connect(self.on_item_changed)
        # Determine if we should reselect something
        if filt != "All" and self.display:
            # current_index = self.view.currentIndex()
            # real_index = self.proxy_model.mapToSource(current_index)
            # obj = self._data[real_index.row()]
            obj = self.display.current
            if obj and (filt != obj.level_nid or (filt == "Global" and obj.level_nid)):
                # Change selection only if we need to!
                first_index = self.proxy_model.index(0, 0)
                self.view.setCurrentIndex(first_index)
                self.set_current_index(first_index)
        self.update_list()

    def update_list(self):
        # self.model.layoutChanged.emit()
        # self.proxy_model.invalidate()
        self.proxy_model.layoutChanged.emit()

class EventProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        self.text_box = CodeEditor(self)
        self.text_box.textChanged.connect(self.text_changed)

        self.find_action = QAction("Find...", self, shortcut="Ctrl+F", triggered=find_and_replace.Find(self).show)
        self.replace_action = QAction("Replace...", self, shortcut="Ctrl+H", triggered=find_and_replace.Find(self).show)
        self.replace_all_action = QAction("Replace all...", self, shortcut="Ctrl+Shift+H", triggered=find_and_replace.Find(self).show)
        self.addAction(self.find_action)
        self.addAction(self.replace_action)
        self.addAction(self.replace_all_action)

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
        self.level_filter_box = left_frame.level_filter_box
        grid = left_frame.layout()

        self.name_box = PropertyBox("Name", QLineEdit, self)
        self.name_box.edit.textChanged.connect(self.name_changed)
        self.name_box.edit.editingFinished.connect(self.name_done_editing)

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
        
        grid.addWidget(QHLine(), 3, 0)
        grid.addWidget(self.name_box, 4, 0)
        grid.addWidget(self.level_nid_box, 5, 0)
        grid.addWidget(self.trigger_box, 6, 0)
        grid.addWidget(self.condition_box, 7, 0)
        grid.addWidget(self.only_once_box, 8, 0, Qt.AlignLeft)

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
                    if region.region_type == 'event':
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

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def name_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        other_names = [d.name for d in self._data.values() if d is not self.current and d.level_nid == self.current.level_nid]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Event ID %s already in use' % self.current.nid)
            self.current.name = str_utils.get_next_name(self.current.name, other_names)
        self._data.update_nid(self.current, self.current.nid, set_nid=False)
        self.window.update_list()

    def trigger_changed(self, idx):
        cur_val = self.trigger_box.edit.currentText()
        if cur_val == 'None':
            self.current.trigger = None
        elif cur_val in [trigger.nid for trigger in event_prefab.all_triggers]:
            self.current.trigger = cur_val
        else:
            self.current.trigger = cur_val
        self.window.update_list()

    def level_nid_changed(self, idx):
        if idx == 0:
            self.current.level_nid = None
            self.show_map_button.setEnabled(False)
            if self.level_filter_box.edit.currentText() != "All":
                self.level_filter_box.edit.setValue("Global")
        else:
            self.current.level_nid = DB.levels[idx - 1].nid
            current_level = DB.levels.get(self.current.level_nid)
            if current_level.tilemap:
                self.show_map_button.setEnabled(True)
            else:
                self.show_map_button.setEnabled(False)
            if self.level_filter_box.edit.currentText() != "All":
                self.level_filter_box.edit.setValue(self.current.level_nid)

        # Update trigger box to match current level
        self.trigger_box.edit.clear()
        if idx == 0:
            self.trigger_box.edit.addItems(self.get_trigger_items("Global"))
        else:
            self.trigger_box.edit.addItems(self.get_trigger_items(self.current.level_nid))
        self.trigger_box.edit.setValue(self.current.trigger)
        self.window.update_list()

    def condition_changed(self, text):
        self.current.condition = text

    def only_once_changed(self, state):
        self.current.only_once = bool(state)

    def text_changed(self):
        self.current.commands.clear()
        text = self.text_box.toPlainText()
        lines = [line.strip() for line in text.splitlines()]
        for line in lines:
            command = event_commands.parse_text(line)
            if command:
                self.current.commands.append(command)

    def set_current(self, current):
        self.current = current
        self.name_box.edit.setText(current.name)
        # self.trigger_box.edit.clear()
        if current.level_nid is not None:
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
        num_tabs = 0
        for command in current.commands:
            if command:
                if command.nid in ('else', 'elif', 'end'):
                    num_tabs -= 1
                text += '    ' * num_tabs
                text += command.to_plain_text()
                text += '\n'
                if command.nid in ('if', 'elif', 'else'):
                    num_tabs += 1
            else:
                print("NoneType in current.commands")

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
