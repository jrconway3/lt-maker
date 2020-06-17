import functools

from PyQt5.QtWidgets import QWidget, QButtonGroup, \
    QListWidgetItem, QRadioButton, QHBoxLayout, QLabel, QListWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.extensions.color_icon import ColorIcon

class PaletteWidget(QWidget):
    def __init__(self, idx, palette, parent=None):
        super().__init__(parent)
        self.window = parent
        self.idx = idx
        self.palette = palette

        self.create_widgets()

    def create_widgets(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        radio_button = QRadioButton()
        self.window.radio_button_group.addButton(radio_button, self.idx)
        radio_button.clicked.connect(lambda: self.window.set_palette(self.idx))

        self.name_label = QLabel(self.palette.nid)

        self.palette_display = QHBoxLayout()
        self.palette_display.setSpacing(0)
        self.palette_display.setContentsMargins(0, 0, 0, 0)

        self.color_icons = []

        for idx, color in enumerate(self.palette.colors):
            qcolor = QColor(*color).name()
            icon = ColorIcon(qcolor, self)
            icon.set_size(16)
            icon.colorChanged.connect(functools.partial(self.on_color_change, idx))
            self.palette_display.addWidget(icon, 0, Qt.AlignCenter)
            self.color_icons.append(icon)

        layout.addWidget(radio_button)
        layout.addWidget(self.name_label)
        layout.addLayout(self.palette_display)

    def on_color_change(self, idx, color):
        color = color.getRgb()
        self.palette.colors[idx] = color[:3]

class PaletteMenu(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self.uniformItemSizes = True

        self.radio_button_group = QButtonGroup()
        self.palettes = []
        self.palette_widgets = []

        self.current_idx = 0

    def set_current(self, palettes):
        self.clear()

        for idx, palette in enumerate(palettes):
            self.palettes.append(palette)
            print(palette)

            item = QListWidgetItem(self)
            pf = PaletteWidget(idx, palette, self)
            self.palette_widgets.append(pf)
            item.setSizeHint(pf.minimumSizeHint())
            self.addItem(item)
            self.setItemWidget(item, pf)
            self.setMinimumWidth(self.sizeHintForColumn(0))

    def set_palette(self, idx):
        self.current_idx = idx
        self.radio_button_group.button(idx).setChecked(True)

    def get_palette(self):
        return self.palettes[self.current_idx]

    def clear(self):
        # self.radio_button_group.clear()
        self.palettes.clear()

        # for idx, l in reversed(list(enumerate(self.palette_widgets))):
        #     self.takeItem(idx)
        #     l.deleteLater()
        super().clear()
        self.current_idx = 0
