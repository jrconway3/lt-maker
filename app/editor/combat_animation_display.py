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

    def nid_change_watchers(self, combat_anim, old_nid, new_nid):
        # What uses combat animations
        # Classes
        for klass in DB.classes:
            if klass.male_combat_anim_nid == old_nid:
                klass.male_combat_anim_nid = new_nid
            if klass.female_combat_anim_nid == old_nid:
                klass.female_combat_anim_nid = new_nid

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
        self.loop = False
        self.counter = 0
        self.frames_passed = 0

        self.anim_view = AnimView(self)

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
        self.new_weapon_button = QPushButton("+", self)
        self.new_weapon_button.clicked.connect(self.add_new_weapon)
        weapon_row.addWidget(self.weapon_box)
        weapon_row.addWidget(self.new_weapon_button)

        pose_row = QHBoxLayout()
        self.pose_box = ComboBox()
        self.pose_box.currentTextChanged.connect(self.pose_changed)
        self.new_pose_button = QPushButton("+", self)
        self.new_pose_button.clicked.connect(self.add_new_pose)
        pose_row.addWidget(self.pose_box)
        pose_row.addWidget(self.new_pose_button)

        info_form.addRow("Unique ID", self.nid_box)
        info_form.addRow("Weapon", weapon_row)
        info_form.addRow("Pose", pose_row)

        view_section.addWidget(self.anim_view)
        view_section.addLayout(button_section)

        main_splitter = QSplitter(self)
        main_splitter.setChildrenCollapsible(False)

        right_splitter = QSplitter(self)
        right_splitter.setOrientation(Qt.Vertical)
        right_splitter.setChilrenCollapsible(False)
        right_splitter.addWidget(self.palette_menu)
        right_splitter.addWidget(self.timeline_menu)

        main_splitter.addWidget(view_frame)
        main_splitter.addWidget(right_splitter)

        final_section = QHBoxLayout()
        self.setLayout(final_section)
        final_section.addWidget(main_splitter)

        TIMER.tick_elapsed.connect(self.tick)

