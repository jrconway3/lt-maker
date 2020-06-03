class CombatAnimDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        title = "Combat Animation"
        right_frame = CombatAnimProperties
        collection_model = CombatAnimModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceListView)
        return dialog

class CombatAnimModel(ResourceCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            animation = self._data[index.row()]
            text = animation.nid
            return text
        elif role == Qt.DecorationRole:
            # TODO create icon out of standing image
            return None
        return None

    def create_new(self):
        nid = utilities.get_next_name('New Combat Anim', self._data.keys())
        new_anim = CombatAnimation(nid)
        self._data.append(new_anim)

    def delete(self, idx):
        # Check to see what is using me?
        res = self._data[idx]
        nid = res.nid
        affected_classes = [klass for klass in DB.classes if klass.male_combat_anim_nid == nid or klass.female_combat_anim_nid == nid]

        if affected_classes:
            affected = Data(affected_classes)
            from app.editor.class_database import ClassModel
            model = ClassModel
            msg = "Deleting Combat Animation <b>%s</b> would affect these classes"
            ok = DeletionDialog.inform(affected, model, msg, self.window)
            if ok:
                pass
            else:
                return
        super().delete(idx)

    def change_nid(self, old_nid, new_nid):
        # What uses combat animations
        # Classes
        for klass in DB.classes:
            if klass.male_combat_anim_nid == old_nid:
                klass.male_combat_anim_nid = new_nid
            if klass.female_combat_anim_nid == old_nid:
                klass.female_combat_anim_nid = new_nid

    def nid_change_watchers(self, combat_anim, old_nid, new_nid):
        self.change_nid(old_nid, new_nid)

class CombatAnimProperties(QWidget):
    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data
        self.resource_editor = self.window.window

        # Populate resources
        for combat_anim in self._data:
            for weapon_anim in combat_anim.weapon_anims:
                for frame in weapon_anim.frames:
                    frame.pixmap = QPixmap(frame.full_path)

        self.current = current
        self.playing = False
        self.paused = False
        self.loop = False
        self.counter = 0
        self.frames_passed = 0

        self.anim_view = IconView(self)

        self.palette_menu = PaletteMenu(self)
        self.palette_menu.palette_changed.connect(self.palette_changed)
        self.timeline_menu = TimelineMenu(self)

        view_section = QVBoxLayout()

        button_section = QHBoxLayout()
        button_section.setAlignment(Qt.AlignTop)

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.stop_button = QToolButton(self)
        self.stop_button.setICon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.stop_button.clicked.connect(self.stop_clicked)

        self.loop_button = QToolButton(self)
        self.loop_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.loop_button.clicked.connect(self.loop_clicked)
        self.loop_button.setCheckable(True)

        label = QLabel("FPS ")

        self.speed_box = QSpinBox(self)
        self.speed_box.setValue(60)
        self.speed_box.setRange(1, 240)
        self.speed_box.valueChanged.connect(self.speed_changed)

        button_section.addWidget(self.play_button)
        button_section.addWidget(self.stop_button)
        button_section.addWidget(self.loop_button)
        button_section.addWidget(label)
        button_section.addWidget(self.speed_box)

        info_form = QFormLayout()

        self.nid_box = QLineEdit()
        self.nid_box.textChanged.connect(self.nid_changed)
        self.nid_box.editingFinished.connect(self.nid_done_editing)

        weapon_row = QHBoxLayout()
        self.weapon_box = ComboBox()
        self.weapon_box.currentTextChanged.connect(self.weapon_changed)
        self.new_weapon_button = QPushButton("+")
        self.new_weapon_button.setMaximumWidth(30)
        self.new_weapon_button.clicked.connect(self.add_new_weapon)
        weapon_row.addWidget(self.weapon_box)
        weapon_row.addWidget(self.new_weapon_button)

        pose_row = QHBoxLayout()
        self.pose_box = ComboBox()
        self.pose_box.currentTextChanged.connect(self.pose_changed)
        self.new_pose_button = QPushButton("+")
        self.new_pose_button.setMaximumWidth(30)
        self.new_pose_button.clicked.connect(self.add_new_pose)
        pose_row.addWidget(self.pose_box)
        pose_row.addWidget(self.new_pose_button)

        info_form.addRow("Unique ID", self.nid_box)
        info_form.addRow("Weapon", weapon_row)
        info_form.addRow("Pose", pose_row)

        frame_group_box = QGroupBox()
        frame_group_box.setTitle("Add Image Frames")
        frame_layout = QVBoxLayout()
        frame_group_box.setLayout(frame_layout)
        self.import_from_lt_button = QPushButton("Import Lion Throne Animation...")
        self.import_from_lt_button.clicked.connect(self.import_lion_throne)
        self.import_from_gba_button = QPushButton("Import GBA Animation...")
        self.import_from_gba_button.clicked.connect(self.import_gba)
        self.import_png_button = QPushButton("Import PNG Images...")
        self.import_png_button.clicked.connect(self.import_png)

        view_section.addWidget(self.anim_view)
        view_section.addLayout(button_section)
        view_section.addLayout(info_form)
        view_section.addWidget(frame_group_box)

        view_frame = QFrame()
        view_frame.setLayout(view_section)

        main_splitter = QSplitter(self)
        main_splitter.setChildrenCollapsible(False)

        right_splitter = QSplitter(self)
        right_splitter.setOrientation(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.addWidget(self.palette_menu)
        right_splitter.addWidget(self.timeline_menu)

        main_splitter.addWidget(view_frame)
        main_splitter.addWidget(right_splitter)

        final_section = QHBoxLayout()
        self.setLayout(final_section)
        final_section.addWidget(main_splitter)

        TIMER.tick_elapsed.connect(self.tick)

    def play(self):
        self.playing = True
        self.paused = False
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def pause(self):
        self.playing = False
        self.paused = True
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def stop(self):
        self.playing = False
        self.paused = False
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def play_clicked(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def stop_clicked(self):
        self.stop()

    def loop_clicked(self, val):
        if val:
            self.loop = True
        else:
            self.loop = False

    def speed_changed(self, val):
        pass

    def nid_changed(self, text):
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        other_nids = [d.nid for d in self._data.value() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'ID %s already in use' % self.current.nid)
            self.current.nid = utilities.get_next_name(self.current.nid, other_nids)
        self.model.change_nid(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def weapon_changed(self, text):
        weapon_anim = self.get_current_weapon_anim()
        poses = self.reset_pose_box(weapon_anim)

        current_pose_nid = self.pose_box.currentText()
        current_pose = poses.get(current_pose_nid)
        frames = weapon_anim.frames
        self.timeline_menu.set_current(current_pose, frames)

    def add_new_weapon(self):
        pass

    def pose_changed(self, text):
        current_pose_nid = self.pose_box.currentText()
        weapon_anim = self.get_current_weapon_anim()
        poses = weapon_anim.poses
        current_pose = poses.get(current_pose_nid)
        self.timeline_menu.set_current_pose(current_pose)

    def add_new_pose(self):
        pass

    def palette_changed(self, palette):
        pass

    def import_lion_throne(self):
        pass

    def import_gba(self):
        pass

    def import_png(self):
        pass

    def get_current_weapon_anim(self):
        weapon_nid = self.weapon_box.currentText()
        return self.current.weapon_anims.get(weapon_nid)

    def reset_pose_box(self, weapon_anim):
        self.pose_box.clear()
        poses = weapon_anim.poses
        self.pose_box.addItems([d.nid for d in poses])
        self.pose_box.setValue(poses[0].nid)
        return poses

    def set_current(self, current):
        self.stop()

        self.current = current
        self.nid_box.setText(self.current.nid)

        self.weapon_box.clear()
        weapon_anims = self.current.weapon_anims
        self.weapon_box.addItems([d.nid for d in weapon_anims])
        self.weapon_box.setValue(weapon_anims[0].nid)

        weapon_anim = self.get_current_weapon_anim()
        poses = self.reset_pose_box(weapon_anim)

        self.palette_menu.set_current(self.current.palettes)

        current_pose_nid = self.pose_box.currentText()
        current_pose = poses.get(current_pose_nid)
        frames = weapon_anim.frames
        self.timeline_menu.set_current(current_pose, frames)

    def modify_for_palette(self, pixmap: QPixmap) -> QPixmap:
        current_palette = self.palette_menu.get_current_palette()
        return pixmap

    def draw_frame(self):
        if self.playing:
            current_frame = self.timeline_menu.get_current_frame()
            current_time = time.time() * 1000
            milliseconds_past = current_time - self.last_update
            fps = self.speed_box.value()
            framerate = 1000 / fps
            num_frames = int(milliseconds_past / framerate)
            unspent_time = milliseconds_past % framerate
            if num_frames >= current_frame.num_frames:
                self.last_update = current_time - unspent_time
                next_frame = self.timeline_menu.get_next_frame()
                if next_frame:
                    self.timeline_menu.set_current_frame(next_frame)
                elif self.loop:
                    first_frame = self.timeline_menu.reset()
                    self.timeline_menu.set_current_frame(first_frame)
                else:
                    self.stop()
        elif self.paused:
            current_frame = self.timeline_menu.get_current_frame()
        else:
            current_frame = self.timeline_menu.get_first_frame()

        # Actually show current frame
        if current_frame:
            pix = self.modify_for_palette(current_frame.pixmap)
            self.anim_view.set_image(pix)
            self.anim_view.show_image()
