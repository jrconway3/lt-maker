import functools

from PyQt5.QtWidgets import QVBoxLayout, QWidget, QAction, QWidgetAction, \
    QListWidgetItem, QLineEdit, QToolButton, QApplication, QMenu, QToolBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from app.data.data import Data
from app.data import combat_animation_command

from app.editor import combat_command_widgets
from app.extensions.widget_list import WidgetList

class TimelineList(WidgetList):
    def add_command_widget(self, command_widget):
        item = QListWidgetItem()
        item.setSizeHint(command_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, command_widget)
        self.index_list.append(command_widget.data)
        return item

    def remove_command(self, command):
        if command in self.index_list:
            idx = self.index_list.index(command)
            self.index_list.remove(command)
            return self.takeItem(idx)
        return None

class TimelineMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        self.current_pose = None
        self.current_frames = None

        self.current_idx = 0

        self.view = TimelineList(self)

        self.create_actions()
        self.create_toolbar()

        self.create_input()

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.view)
        layout.addWidget(self.entry)
        self.setLayout(layout)

    def set_current(self, pose, frames):
        self.current_frames = frames
        self.current_pose = pose
        self.current_idx = 0

        for idx, command in enumerate(self.current_pose.timeline):
            self.add_command(command)

        self.highlight(self.current_idx)

    def highlight(self, idx):
        self.view.item(idx).setBackground(Qt.yellow, Qt.SolidPattern)

    def inc_current_idx(self):
        self.current_idx += 1
        self.highlight(self.current_idx)

    def reset(self):
        self.current_idx = 0
        self.highlight(self.current_idx)

    def add_command(self, command):
        command_widget = \
            combat_command_widgets.get_command_widget(command, self)
        self.view.add_command(command_widget)

    def add_text(self):
        try:
            text = self.entry.text()
            split_text = text.split(';')
            command = combat_animation_command.parse_text(split_text)
            self.add_command(command)                
            self.entry.clear()
        except Exception:
            # play error sound
            print("You got an error, boi!", flush=True)
            QApplication.beep()

    def create_actions(self):
        self.actions = {}
        for command in combat_animation_command.anim_commands:
            new_func = functools.partial(self.add_command, command)
            new_action = QAction(QIcon(), command.name, self, triggered=new_func)
            self.actions[command.nid] = new_action

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.menus = {}

        for command in combat_animation_command.anim_commands:
            if command.tag not in self.menus:
                new_menu = QMenu(self)
                self.menus[command.tag] = new_menu
                toolbutton = QToolButton(self)
                toolbutton.setIcon(QIcon("icons/command_%s.png" % command.tag))
                toolbutton.setMenu(new_menu)
                toolbutton.setPopupMode(QToolButton.InstantPopup)
                toolbutton_action = QWidgetAction(self)
                toolbutton_action.setDefaultWidget(toolbutton)
                self.toolbar.addAction(toolbutton_action)
            menu = self.menus[command.tag]
            menu.addAction(self.actions.get(command.nid))

    def create_input(self):
        self.entry = QLineEdit(self)
        self.entry.setPlaceholderText("Enter command here")
        self.entry.returnPressed.connect(self.add_text)

    def get_command(self, idx):
        if not self.current_pose:
            return None
        command = self.current_pose.timeline[idx]
        while command.tag not in ('frame', 'wait'):
            idx += 1
            if idx < len(self.current_pose.timeline):
                command = self.current_pose.timeline[idx]
            else:
                return None
        return command

    def get_current_command(self):
        return self.current_pose.timeline[self.current_idx]

    def get_first_command_frame(self):
        """
        Returns the first frame that would be shown to the user in an animation
        """
        return self.get_command(0)
