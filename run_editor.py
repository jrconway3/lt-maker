import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# testindex == self.window.view.currentIndex()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('main_icon.ico'))
    from app.editor.main_editor import MainEditor
    window = MainEditor()
    window.show()
    app.exec_()
