try:
    import cPickle as pickle
except ImportError:
    import pickle

from PyQt5.QtWidgets import QVBoxLayout, QDialog, QTextEdit
from PyQt5.QtGui import QTextCursor
from app.extensions.custom_gui import PropertyBox, ComboBox, Dialog

class SaveViewer(Dialog):
    def __init__(self, saves, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Save")
        self.window = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.save_box = PropertyBox("Save", ComboBox, self)
        self.save_box.edit.addItems(saves)
        self.save_box.edit.activated.connect(self.save_changed)
        layout.addWidget(self.save_box)

        self.display_box = PropertyBox("Info", QTextEdit, self)
        layout.addWidget(self.display_box)

        layout.addWidget(self.buttonbox)

        self.save_changed()

    def save_changed(self):
        save_loc = self.save_box.edit.currentText()
        meta_loc = save_loc + 'meta'
        with open(save_loc, 'rb') as fp:
            s_dict = pickle.load(fp)
        with open(meta_loc, 'rb') as fp:
            meta_dict = pickle.load(fp)
        level_nid = meta_dict['level_nid']
        level_name = meta_dict['level_title']
        time = meta_dict.get('time')
        self.display_box.edit.clear()
        text = 'Level %s: %s\n' % (level_nid, level_name)
        self.display_box.edit.insertPlainText(text)
        if time:
            text = 'Saved: %s\n' % time
            self.display_box.edit.insertPlainText(text)
        self.display_box.edit.insertPlainText("Units:\n")
        item_registry = {i['uid']: i['nid'] for i in s_dict['items']}
        for unit in s_dict['units']:
            if not unit['dead'] and unit['team'] == 'player':
                items = ', '.join(item_registry.get(item) for item in unit['items'])
                unit_text = '%s Lv %d Exp %d Items: %s\n' % (unit['nid'], unit['level'], unit['exp'], items)

                self.display_box.edit.insertPlainText(unit_text)

        self.display_box.edit.moveCursor(QTextCursor.Start)
        self.display_box.edit.ensureCursorVisible()

    @classmethod
    def get(cls, saves, parent=None):
        dialog = cls(saves, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.save_box.edit.currentText()
        else:
            return None
