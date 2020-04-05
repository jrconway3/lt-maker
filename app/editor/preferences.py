from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QSettings

from app.extensions.custom_gui import ComboBox, PropertyBox, Dialog

name_to_button = {'L-click': Qt.LeftButton,
                  'R-click': Qt.RightButton}
button_to_name = {v: k for k, v in name_to_button.items()}

class PreferencesDialog(Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.settings = QSettings('rainlash', 'Lex Talionis')

        self.saved_preferences = {}
        self.saved_preferences['select_button'] = self.settings.value('select_button', Qt.LeftButton)
        self.saved_preferences['place_button'] = self.settings.value('place_button', Qt.RightButton)

        self.available_options = name_to_button.keys()

        label = QLabel("Modify mouse preferences for Terrain and Unit Painter Menus")

        self.select = PropertyBox('Select', ComboBox, self)
        for option in self.available_options:
            self.select.edit.addItem(option)
        self.place = PropertyBox('Place', ComboBox, self)
        for option in self.available_options:
            self.place.edit.addItem(option)
        self.select.edit.setValue(button_to_name[self.saved_preferences['select_button']])
        self.place.edit.setValue(button_to_name[self.saved_preferences['place_button']])
        self.select.edit.currentIndexChanged.connect(self.select_changed)
        self.place.edit.currentIndexChanged.connect(self.place_changed)

        self.layout.addWidget(label)
        self.layout.addWidget(self.select)
        self.layout.addWidget(self.place)
        self.layout.addWidget(self.buttonbox)

    def select_changed(self, idx):
        choice = self.select.edit.currentText()
        if choice == 'L-click':
            self.place.edit.setValue('R-click')
        else:
            self.place.edit.setValue('L-click')

    def place_changed(self, idx):
        choice = self.place.edit.currentText()
        if choice == 'L-click':
            self.select.edit.setValue('R-click')
        else:
            self.select.edit.setValue('L-click')

    def accept(self):
        self.settings.setValue('select_button', name_to_button[self.select.edit.currentText()])
        self.settings.setValue('place_button', name_to_button[self.place.edit.currentText()])
        super().accept()

    def reject(self):
        super().reject()
