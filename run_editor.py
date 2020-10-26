import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings

# testindex == self.window.view.currentIndex()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('main_icon.ico'))
    from app import dark_theme
    settings = QSettings('rainlash', 'Lex Talionis')
    theme = settings.value('theme', 0)
    if theme == 0:
        pass
    elif theme == 1:
        d = dark_theme.QDarkPalette()
        d.set_app(app)
    elif theme == 2:
        d = dark_theme.QDiscordPalette()
        d.set_app(app)
    elif theme == 3:
        d = dark_theme.QDarkBGPalette()
        d.set_app(app)
    elif theme == 4:
        d = dark_theme.QBlueBGPalette()
        d.set_app(app)
    from app.editor.main_editor import MainEditor
    window = MainEditor()
    if theme == 3:
        window.setStyleSheet("QDialog {background-image:url(bg.png)};")
    elif theme == 4:
        window.setStyleSheet("QDialog {background-image:url(bg2.png)};")
    window.show()
    app.exec_()
