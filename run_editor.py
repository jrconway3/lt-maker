import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings

# testindex == self.window.view.currentIndex()
if __name__ == '__main__':
    ap = QApplication(sys.argv)
    ap.setWindowIcon(QIcon('main_icon.ico'))
    from app import dark_theme
    settings = QSettings('rainlash', 'Lex Talionis')
    theme = settings.value('theme', 0)
    dark_theme.set(ap, theme)
    from app.editor.main_editor import MainEditor
    window = MainEditor()
    window.show()
    ap.exec_()
