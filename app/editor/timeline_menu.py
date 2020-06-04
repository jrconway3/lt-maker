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
        self.curent_frames = None

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

    def add_command(self, command):
        command_widget = combat_command_widgets.get_command_widget(command, self)
        self.view.add_command(command)

    def parse_text(self, attr, text):
        if attr is None:
            return None
        elif attr is int:
            return int(text)
        elif attr == 'color':
            return tuple(int(_) for _ in text.split(','))
        elif attr == 'frame':
            return text

    def add_text(self):
        try:
            text = self.entry.text()
            split_text = text.split(';')
            command_nid = split_text[0]
            command = combat_animation_command.get_command(command_nid)
            values = []
            for idx, attr in enumerate(command.attr):
                value = self.parse_text(attr, split_text[idx])
                values.append(value)
            if len(values) == 0:
                pass
            elif len(values) == 1:
                command.value = values[0]
            elif len(values) > 1:
                command.value = tuple(values)
            self.add_command(command)                
            self.entry.clear()
        except Exception:
            # play error sound?
            return

    def create_actions(self):
        self.actions = Data()
        for command in combat_animation_command.anim_commands:
            self.actions[command.nid] = \
                QAction(command.name,
                        triggered=functools.partial(self.add_command, command))

    def create_toolbar(self):
        self.toolbar = QToolBar(self)
        self.menus = {}

        for command in combat_animation_command.anim_commands:
            if command.tag not in self.menus:
                new_menu = QMenu(self)
                self.menus[command.tag] = new_menu
                toolbutton = QToolButton(self)
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

    def get_frame(self, idx):
        frame = self.current_pose.timeline[idx]
        while frame.tag != 'frame':
            idx += 1
            if idx < len(self.current_pose.timeline):
                frame = self.current_pose.timeline[idx]
            else:
                return None
        if frame.nid == 'frame':
            return frame.value[0], frame.value[1]
        else:
            return frame.value, None

    def get_current_frame(self):
        """
        Returns the frame that should be shown the user at this moment
        """
        return self.get_frame(self.current_idx)

    def get_first_frame(self):
        """
        Returns the first frame that would be shown to the user in an animation
        """
        return self.get_frame(0)

    def parse_command(self, command):
        pass

    def get_next_frame(self):
        """
        Processes the next timeline shenanigans until a new frame is reached
        and then returns that frame
        """
        self.current_idx += 1
        self.highlight(self.current_idx)
        script = self.poses.timeline
        while self.current_idx < len(script):
            command = script[self.current_idx]
            self.parse_command(command)
            if command.nid == 'frame':
                num_frames, frame = command.value
                return num_frames, frame
            else:  # Wait
                return command.value, None
        return None, None
