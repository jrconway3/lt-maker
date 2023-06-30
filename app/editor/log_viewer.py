import io
import sys
from PyQt5 import QtGui

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QMenu, QAction, QPushButton, QGridLayout, QLabel
from PyQt5.QtGui import QWindow

from app import lt_log
import os


class LogViewer(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle("Logs")
        self.resize(800,800)

        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setFont(QFont('Consolas', 10))
        self.textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)

        log_file = lt_log.get_log_fname()
        if log_file:
            self.log_name = os.path.basename(log_file)
            self.log_file_pointer = open(log_file, 'r')
        else:
            self.log_name = "UNKNOWN"
            self.log_file_pointer = io.StringIO("No log file found!")

        self.open_log_button = QPushButton("Open Log Location")
        self.open_log_button.clicked.connect(self.open_log_location)

        self.log_name_label = QLabel(self.log_name)

        self.fetch_log_timer = QTimer(self)
        self.fetch_log_timer.timeout.connect(self.fetch_log)
        self.fetch_log_timer.start(500)
        self.fetch_log()

        layout = QVBoxLayout()
        layout.addWidget(self.log_name_label)
        layout.addWidget(self.textEdit)
        layout.addWidget(self.open_log_button)
        self.setLayout(layout)

    def open_log_location(self):
        log_file = lt_log.get_log_fname()
        if log_file:
            os.startfile(os.path.dirname(log_file))

    def fetch_log(self):
        if self.log_file_pointer.closed:
            return
        lines = []
        line = self.log_file_pointer.readline()
        while line:
            lines.append(line)
            line = self.log_file_pointer.readline()
        vscroll = self.textEdit.verticalScrollBar()
        at_bottom = (vscroll.value() >= (vscroll.maximum() - 4))
        prev_scroll = vscroll.value()
        self.textEdit.moveCursor(QTextCursor.End)
        self.textEdit.insertPlainText(''.join(lines))
        if not at_bottom:
            vscroll.setValue(prev_scroll)
        else:
            vscroll.setValue(vscroll.maximum())

    def closeEvent(self, a0) -> None:
        self.log_file_pointer.close()
        return super().closeEvent(a0)

def show_logs():
    dlg = LogViewer()
    dlg.show()
    return dlg

if __name__ == '__main__':
        app = QApplication(sys.argv)
        win = LogViewer()
        win.show()
        sys.exit(app.exec_())