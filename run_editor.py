import sys

from app.editor.settings import MainSettingsController

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

if __name__ == '__main__':
    # Hack to get a Windows icon to show up
    try:
        import ctypes
        myappid = u'rainlash.lextalionis.ltmaker.current' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        print("Maybe not Windows?")

    ap = QApplication(sys.argv)
    ap.setWindowIcon(QIcon('favicon.ico'))
    from app import dark_theme
    settings = MainSettingsController()
    theme = settings.get_theme(0)
    dark_theme.set(ap, theme)
    from app.editor.main_editor import MainEditor
    window = MainEditor()
    window.show()
    ap.exec_()
