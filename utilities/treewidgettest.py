import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class displayItem(QtWidgets.QWidget):
    def __init__(self, num):
        QtWidgets.QWidget.__init__(self)
        self.size = 100
        self.resize(self.size, self.size)
        self.setMinimumSize(self.size, self.size)
        self.text = num

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.drawText(self.size//2, self.size//2, str(self.text))

app = QtWidgets.QApplication(sys.argv)
widget = QtWidgets.QTreeWidget()
widget.setWindowTitle('simple tree')

# Build the list widgets
treeItem1 = QtWidgets.QTreeWidgetItem(widget)
treeItem1.setText(0, "TreeWidget Parent")  # Sets the "header" for your [+] box

list1 = QtWidgets.QListWidget()  # This will contain your icon list
list1.setMovement(QtWidgets.QListView.Static)  # otherwise the icons are draggable
list1.setResizeMode(QtWidgets.QListView.Adjust)  # Redo layout every time we resize

for i in range(3):
    listItem = QtWidgets.QListWidgetItem(list1)
    list1.setItemWidget(listItem, displayItem(i))

list1.setAutoFillBackground(True)  # Required for a widget that will be a QTreeWidgetItem widget
treeSubItem1 = QtWidgets.QTreeWidgetItem(treeItem1)  # Make a subitem to hold our list
widget.setItemWidget(treeSubItem1, 0, list1)  # Assign this list as a tree item

treeItem2 = QtWidgets.QTreeWidgetItem(widget)  # Make a fake second parent
treeItem2.setText(0, "TreeWidget Parent II")

widget.show()
sys.exit(app.exec_())
