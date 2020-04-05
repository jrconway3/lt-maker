from functools import partial

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPalette

from app.extensions.custom_gui import ComboBox

class MultiComboBoxList(QListWidget):
    item_changed = pyqtSignal()

    def __init__(self, data, pixmap_func, parent):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.pixmap_func = pixmap_func
        self.index_list = []
        self.combo_box_list = []

    def length(self):
        return len(self.index_list)

    def add_item(self, item_nid):
        new_box = QListWidgetItem()
        combo_box = ComboBox(self)
        for i in self._data:
            if self.pixmap_func:
                pix = self.pixmap_func(i)
                icon = QIcon(pix) if pix else None
                combo_box.addItem(icon, i.nid)
            else:
                combo_box.addItem(i.nid)
        combo_box.setValue(item_nid)
        self.addItem(new_box)
        self.setItemWidget(new_box, combo_box)
        corrected_item_nid = combo_box.currentText()
        self.index_list.append(corrected_item_nid)
        self.combo_box_list.append(combo_box)
        idx = len(self.combo_box_list) - 1
        combo_box.currentIndexChanged.connect(partial(self.on_item_change, idx))
        # print("ItemList Add Item: Index List")
        # print(self.index_list, flush=True)
        return corrected_item_nid

    def remove_item(self, item_nid):
        if item_nid in self.index_list:
            idx = self.index_list.index(item_nid)
            self.index_list.remove(item_nid)
            self.combo_box_list.pop(idx)
            return self.takeItem(idx)
        return None

    def remove_item_at_index(self, idx):
        if len(self.index_list) > idx:
            self.index_list.pop(idx)
            self.combo_box_list.pop(idx)
            return self.takeItem(idx)
        return None

    def clear(self):
        super().clear()
        self.index_list.clear()
        self.combo_box_list.clear()

    def set_current(self, items):
        # print("ItemList Set Current")
        # print(items, flush=True)
        self.clear()
        # print("ItemList Set Current")
        # print(items, flush=True)
        for i in items:
            self.add_item(i)
        self.item_changed.emit()

    def on_item_change(self, index):
        # print("ItemList Item Change")
        # print(index, flush=True)
        combo_box = self.combo_box_list[index]
        item_nid = combo_box.currentText()
        # print(item_nid, flush=True)
        self.index_list[index] = item_nid
        self.item_changed.emit()

    def set_color(self, color_list):
        print(color_list, flush=True)
        for idx, box in enumerate(self.combo_box_list):
            palette = box.palette()
            if color_list[idx]:
                palette.setColor(QPalette.Text, Qt.red)
            else:
                palette.setColor(QPalette.Text, Qt.black)
            box.setPalette(palette)
