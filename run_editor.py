import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from app.editor.main_editor import MainEditor

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('main_icon.ico'))
    window = MainEditor()
    window.show()
    app.exec_()
