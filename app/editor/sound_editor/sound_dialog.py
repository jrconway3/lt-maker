from PyQt5.QtWidgets import QLineEdit, QMessageBox, QVBoxLayout

from app.utilities import str_utils
from app.extensions.custom_gui import PropertyBox, Dialog

class ModifySFXDialog(Dialog):
    def __init__(self, data, current, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modify SFX")
        self.window = parent
        self._data = data
        self.current = current

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.nid_box = PropertyBox("Name", QLineEdit, self)
        layout.addWidget(self.nid_box)

        if len(self.current) > 1:
            self.nid_box.setText("Multiple SFX")
            self.nid_box.setEnabled(False)
        else:
            self.nid_box.setText(self.current[0].nid)
            self.nid_box.edit.textChanged.connect(self.nid_changed)
            self.nid_box.edit.editingFinished.connect(self.nid_done_editing)

        self.tag_box = PropertyBox("Tag", QLineEdit, self)
        tags = [d.tag for d in self.current]
        if len(tags) > 1:
            self.tag_box.setText("Multiple Tags")
        else:
            self.tag_box.setText(self.current[0].tag)
        self.tag_box.edit.textChanged.connect(self.tag_changed)
        layout.addWidget(self.tag_box)

        layout.addWidget(self.buttonbox)

    def nid_changed(self, text):
        for d in self.current:
            d.nid = text

    def nid_done_editing(self):
        current = self.current[0]
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not current]
        if current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'SFX ID %s already in use' % current.nid)
            current.nid = str_utils.get_next_name(current.nid, other_nids)
        self._data.update_nid(current, current.nid)

    def tag_changed(self, text):
        for d in self.current:
            d.tag = text
