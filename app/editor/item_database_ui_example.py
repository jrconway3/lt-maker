from PyQt5.QtWidgets import QDialog
from PyQt5 import uic

qtcreator_file = "item_database.ui"
ui_dialog, qtbaseclass = uic.loadUiType(qtcreator_file)

class ItemDatabase(QDialog, ui_dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=None)
        ui_dialog.__init__(self)

        self.setupUi(self)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ItemDatabase()
    window.show()
    app.exec_()
