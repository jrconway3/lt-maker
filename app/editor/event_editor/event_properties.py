from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QHBoxLayout, QVBoxLayout, \
    QPlainTextEdit
from PyQt5.QtGui import QSyntaxHighlighter, QFont, QTextCharFormat
from PyQt5.QtCore import QRegularExpression, Qt

from app.extensions.custom_gui import PropertyBox, QHLine, ComboBox

from app.data.database import DB
from app.utilities import str_utils
from app.events import event_prefab, event_commands, event_validators

@dataclass
class Rule():
    pattern: QRegularExpression
    _format: QTextCharFormat

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlight_rules = []

        function_head_format = QTextCharFormat()
        function_head_format.setForeground(Qt.blue)
        function_head_format.setFontItalic(True)
        self.function_head_rule = Rule(
            QRegularExpression("^(.*?);"), function_head_format)
        self.highlight_rules.append(self.function_head_rule)

        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.darkGray)
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
        lint_format.setUnderlineColor(Qt.red)
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
        command = event_commands.parse_text(line)
        if command:
            broken_args = []
            values = command.values
            num_keywords = len(command.keywords)
            true_values = values[:num_keywords]
            for idx, value in enumerate(true_values):
                validator = command.keywords[idx]
                text = event_validators.validate(validator, value)
                if text is None:
                    broken_args.append(idx + 1)
            return broken_args
        else:
            return [0]  # First arg is broken

class EventProperties(QWidget):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data

        self.current = current

        self.text_box = QPlainTextEdit(self)
        self.text_box.textChanged.connect(self.text_changed)
        self.text_box.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Text setup
        self.cursor = self.text_box.cursor()
        self.font = QFont()
        self.font.setFamily("Courier")
        self.font.setFixedPitch(True)
        self.font.setPointSize(10)
        self.text_box.setFont(self.font)
        self.highlighter = Highlighter(self.text_box.document())

        main_section = QHBoxLayout()
        self.setLayout(main_section)
        main_section.addWidget(self.text_box)

        left_frame = self.window.left_frame
        grid = left_frame.layout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)

        self.trigger_box = PropertyBox("Trigger", ComboBox, self)
        self.trigger_box.edit.addItem("None")
        self.trigger_box.edit.addItems(event_prefab.all_triggers)
        self.trigger_box.edit.currentIndexChanged.connect(self.trigger_changed)

        self.level_nid_box = PropertyBox("Level", ComboBox, self)
        self.level_nid_box.edit.addItem("Global")
        self.level_nid_box.edit.addItems(DB.levels.keys())
        self.level_nid_box.edit.currentIndexChanged.connect(self.level_nid_changed)

        self.condition_box = PropertyBox("Condition", QLineEdit, self)
        self.condition_box.edit.textChanged.connect(self.condition_changed)
        
        grid.addWidget(QHLine(), 2, 0)
        grid.addWidget(self.nid_box, 3, 0)
        grid.addWidget(self.level_nid_box, 4, 0)
        grid.addWidget(self.trigger_box, 5, 0)
        grid.addWidget(self.condition_box, 6, 0)

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
        if idx == 0:
            self.current.trigger = None
        else:
            self.current.trigger = event_prefab.all_triggers[idx - 1]

    def level_nid_changed(self, idx):
        if idx == 0:
            self.current.level_nid = None
        else:
            self.current.level_nid = DB.levels[idx - 1]

    def condition_changed(self, text):
        self.current.condition = text

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
        if current.level_nid:
            self.level_nid_box.edit.setValue(current.level_nid)
        else:
            self.level_nid_box.edit.setValue('None')
        self.trigger_box.edit.setValue(current.trigger)
        self.condition_box.edit.setText(current.condition)

        # Convert text
        text = ''
        for command in current.commands:
            text += command.to_plain_text()
            text += '\n'

        self.text_box.setPlainText(text)
