import os, glob, time

from PyQt5.QtWidgets import QSplitter, QFrame, QVBoxLayout, \
    QWidget, QGroupBox, QFormLayout, QSpinBox, QFileDialog, \
    QMessageBox, QStyle, QHBoxLayout, QPushButton, QLineEdit, \
    QLabel, QToolButton
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QImage, QPixmap, QIcon, qRgb

from app.data.data import Data
from app.data.resources import RESOURCES
from app.data.database import DB
from app.data import combat_animation, combat_animation_command

from app.editor.timer import TIMER
from app.editor.icon_display import IconView
from app.editor.base_database_gui import DatabaseTab, ResourceCollectionModel
from app.editor.palette_display import PaletteMenu
from app.editor.timeline_menu import TimelineMenu
from app.extensions.custom_gui import ResourceListView, ComboBox, DeletionDialog

import app.editor.utilities as editor_utilities
from app import utilities

class CombatAnimDisplay(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.combat_anims
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
        new_anim = combat_animation.CombatAnimation(nid)
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
        # self.palette_menu.palette_changed.connect(self.palette_changed)
        self.timeline_menu = TimelineMenu(self)

        view_section = QVBoxLayout()

        button_section = QHBoxLayout()
        button_section.setAlignment(Qt.AlignTop)

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.stop_button = QToolButton(self)
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
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

        variant_row = QHBoxLayout()
        self.variant_box = ComboBox()
        self.variant_box.currentIndexChanged.connect(self.variant_changed)
        self.new_variant_button = QPushButton("+")
        self.new_variant_button.setMaximumWidth(30)
        self.new_variant_button.clicked.connect(self.add_new_variant)
        self.delete_variant_button = QPushButton()
        self.delete_variant_button.setIcon(QIcon("icons/x.png"))
        self.delete_variant_button.clicked.connect(self.delete_variant)
        variant_row.addWidget(self.variant_box)
        variant_row.addWidget(self.new_variant_button)
        variant_row.addWidget(self.delete_variant_button)

        weapon_row = QHBoxLayout()
        self.weapon_box = ComboBox()
        self.weapon_box.currentIndexChanged.connect(self.weapon_changed)
        self.new_weapon_button = QPushButton("+")
        self.new_weapon_button.setMaximumWidth(30)
        self.new_weapon_button.clicked.connect(self.add_new_weapon)
        self.delete_weapon_button = QPushButton()
        self.delete_weapon_button.setIcon(QIcon("icons/x.png"))
        self.delete_weapon_button.clicked.connect(self.delete_weapon)
        weapon_row.addWidget(self.weapon_box)
        weapon_row.addWidget(self.new_weapon_button)
        weapon_row.addWidget(self.delete_weapon_button)

        pose_row = QHBoxLayout()
        self.pose_box = ComboBox()
        self.pose_box.currentIndexChanged.connect(self.pose_changed)
        self.new_pose_button = QPushButton("+")
        self.new_pose_button.setMaximumWidth(30)
        self.new_pose_button.clicked.connect(self.add_new_pose)
        self.delete_pose_button = QPushButton()
        self.delete_pose_button.setIcon(QIcon("icons/x.png"))
        self.delete_pose_button.clicked.connect(self.delete_pose)
        pose_row.addWidget(self.pose_box)
        pose_row.addWidget(self.new_pose_button)
        pose_row.addWidget(self.delete_pose_button)

        info_form.addRow("Unique ID", self.nid_box)
        info_form.addRow("Weapon", weapon_row)
        info_form.addRow("Pose", pose_row)

        frame_group_box = QGroupBox()
        frame_group_box.setTitle("Add Image Frames")
        frame_layout = QVBoxLayout()
        frame_group_box.setLayout(frame_layout)
        self.import_from_lt_button = QPushButton("Import Lion Throne Weapon Animation...")
        self.import_from_lt_button.clicked.connect(self.import_lion_throne)
        self.import_from_gba_button = QPushButton("Import GBA Weapon Animation...")
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

    def tick(self):
        self.draw_frame()

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

    def ask_permission(self, obj, text: str) -> bool:
        ret = QMessageBox.warning(self, "Deletion Warning", 
                                  "Really delete %s <b>%s</b>?" % (text, obj.nid),
                                  QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            return True
        else:
            return False

    def variant_changed(self, text):
        variant = self.get_current_variant()
        self.reset_weapon_box(variant)
        weapon_anim = self.get_current_weapon_anim()
        poses = self.reset_pose_box(weapon_anim)

        current_pose_nid = self.pose_box.currentText()
        current_pose = poses.get(current_pose_nid)
        frames = weapon_anim.frames
        self.timeline_menu.set_current(current_pose, frames)

    def add_new_variant(self):
        new_nid = utilities.get_next_name('Variant', self.current.variants.keys())
        new_variant = combat_animation.CombatVariant(new_nid)
        self.current.variants.append(new_variant)
        self.variant_box.addItem(new_nid)
        self.variant_box.setValue(new_nid)

    def delete_variant(self):
        variant = self.get_current_variant()
        if self.ask_permission(variant, 'Variant'):
            self.current.variants.delete(variant)
            self.set_current(self.current)

    def weapon_changed(self, idx):
        weapon_anim = self.get_current_weapon_anim()
        poses = self.reset_pose_box(weapon_anim)

        current_pose_nid = self.pose_box.currentText()
        current_pose = poses.get(current_pose_nid)
        frames = weapon_anim.frames
        self.timeline_menu.set_current(current_pose, frames)

    def add_new_weapon(self):
        variant = self.get_current_variant()
        new_nid = utilities.get_next_name('Weapon', variant.weapon_anims.keys())
        new_weapon = combat_animation.WeaponAnimation(new_nid)
        variant.append(new_weapon)
        self.weapon_box.addItem(new_nid)
        self.weapon_box.setValue(new_nid)

    def delete_weapon(self):
        weapon = self.get_current_weapon_anim()
        if self.ask_permission(weapon, 'Weapon Animation'):
            variant = self.get_current_variant()
            variant.delete(weapon)
            self.reset_weapon_box()
            self.reset_pose_box()

    def pose_changed(self, idx):
        current_pose_nid = self.pose_box.currentText()
        weapon_anim = self.get_current_weapon_anim()
        poses = weapon_anim.poses
        current_pose = poses.get(current_pose_nid)
        self.timeline_menu.set_current_pose(current_pose)

    def add_new_pose(self):
        weapon_anim = self.get_current_weapon_anim()
        new_nid = utilities.get_next_name('Pose', weapon_anim.poses.keys())
        new_pose = combat_animation.Pose(new_nid)
        weapon_anim.append(new_pose)
        self.pose_box.addItem(new_nid)
        self.pose_box.setValue(new_nid)

    def delete_pose(self):
        weapon_anim = self.get_current_weapon_anim()
        pose = weapon_anim.poses.get(self.pose_box.currentText())
        if self.ask_permission(pose, 'Pose'):
            weapon_anim.poses.delete(pose)
            self.reset_pose_box()

    def palette_changed(self, palette):
        pass

    def import_lion_throne(self):
        settings = QSettings("rainlash", "Lex Talionis")
        starting_path = str(settings.value("last_open_path", QDir.currentPath()))
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Lion Throne Script Files", starting_path, "Script Files (*-Script.txt);;All Files (*)")
        if ok:
            for fn in fns:
                if fn.endswith('-Script.txt'):
                    kind = os.path.split(fn)[-1].replace('-Script.txt', '')
                    nid, weapon = kind.split('-')[0]
                    variant_nid = int(nid[-1])
                    if variant_nid == 0:
                        variant_nid = "Male"
                    elif variant_nid == 5:
                        variant_nid = "Female"
                    else:
                        variant_nid = "?"
                    nid = nid[:-1]
                    index_fn = fn.replace('-Script.txt', '-Index.txt')
                    if not os.path.exists(index_fn):
                        QMessageBox.error("Could not find associated index file: %s" % index_fn)
                        continue
                    palettes = glob.glob(fn.replace('-Script.txt', '-*.png'))
                    if not palettes:
                        QMessageBox.error("Could not find any associated palettes")
                        continue
                    palette_nids = []
                    for palette_fn in palettes:
                        palette_nid = os.path.split(palette_fn)[-1][:-4].split('-')[-1]
                        palette_nids.append(palette_nid)
                        print(palette_nid)
                        if palette_nid not in self.current.palettes:
                            palette_colors = editor_utilities.find_palette(QImage(palette_fn))
                            new_palette = combat_animation.Palette(palette_nid, palette_colors)
                            self.current.palettes.append(new_palette)
                    # Get the current variant_nid
                    if variant_nid not in self.current.variants:
                        variant = combat_animation.CombatVariant(variant_nid)
                        self.current.variants.append(variant)
                    else:
                        variant = self.current.variants.get(variant_nid)
                    new_weapon = combat_animation.WeaponAnimation(weapon)
                    # Now add frames to weapon animation
                    with open(index_fn, encoding='utf-8') as index_fp:
                        index_lines = [line.strip() for line in index_fp.readlines()]
                        index_lines = [l.split(';') for l in index_lines]
                    # Use the first palette
                    main_pixmap = QPixmap(palettes[0])
                    for i in index_lines:
                        nid = i[0]
                        x, y = [int(_) for _ in i[1].split(',')]
                        width, height = [int(_) for _ in i[2].split(',')]
                        offset_x, offset_y = [int(_) for _ in i[3].split(',')]
                        new_pixmap = main_pixmap.copy(x, y, width, height)
                        # Need to convert to universal base palette
                        im = new_pixmap.toImage()
                        im = editor_utilities.color_convert(im, self.current.palettes[0].colors, combat_animation.base_palette)
                        new_pixmap = QPixmap.fromImage(im)
                        new_frame = combat_animation.Frame(nid, (offset_x, offset_y), pixmap=new_pixmap)
                        new_weapon.frames.append(new_frame)
                    # Now add poses to the weapon anim
                    with open(fn, encoding='utf-8') as script_fp:
                        script_lines = [line.strip() for line in script_fp.readlines()]
                        script_lines = [line.split(';') for line in script_lines if line and not line.startswith('#')]
                    current_pose = None
                    for line in script_lines:
                        if line[0] == 'pose':
                            current_pose = combat_animation.Pose(line[1])
                            new_weapon.poses.append(current_pose)
                        else:
                            command = combat_animation_command.parse_text(line)
                            current_pose.timeline.append(command)
                    print("Done!!! %s" % fn)
            # Reset
            self.set_current(self.current)

    def import_gba(self):
        pass

    def import_png(self):
        pass

    def get_current_variant(self):
        variant_nid = self.variant_box.currentText()
        return self.current.variants.get(variant_nid)

    def get_current_weapon_anim(self):
        variant = self.get_current_variant()
        weapon_nid = self.weapon_box.currentText()
        return variant.get(weapon_nid)

    def reset_weapon_box(self, variant):
        self.weapon_box.clear()
        weapon_anims = variant.weapon_anims
        self.weapon_box.addItem([d.nid for d in weapon_anims])
        self.weapon_box.setValue(weapon_anims[0].nid)
        return weapon_anims

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

        self.variant_box.clear()
        variants = self.current.variants
        self.variant_box.addItems([d.nid for d in variants])
        self.variant_box.setValue(variants[0].nid)

        variant = self.get_current_variant()

        self.weapon_box.clear()
        weapon_anims = variant.weapon_anims
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
        current_palette = self.palette_menu.get_palette()
        im = pixmap.toImage()
        im_palette = combat_animation.base_palette
        im = editor_utilities.convert_colorkey(im)
        conv_dict = {qRgb(*a): qRgb(*b) for a, b in zip(im_palette.colors, current_palette.colors)}
        im = editor_utilities.color_convert(im, conv_dict)
        pixmap = QPixmap.fromImage(im)
        return pixmap

    def process(self):
        def proceed():
            self.last_update = current_time - unspent_time
            next_command = self.timeline_menu.inc_current_idx()
            if next_command:
                pass
            elif self.loop:
                self.timeline_menu.reset()
                next_command = self.timeline_menu.inc_current_idx()
            else:
                self.stop()
                return None
            return next_command

        if self.playing:
            current_time = time.time() * 1000
            framerate = 1000 / self.speed_box.value()
            milliseconds_past = current_time - self.last_update
            num_frames = int(milliseconds_past / framerate)
            unspent_time = milliseconds_past % framerate

            current_command = self.timeline_menu.get_current_command()

            while current_command:
                if current_command.nid == 'frame':
                    time_to_display, image = current_command.value
                    if num_frames >= time_to_display:
                        current_command = proceed()
                    else:
                        break  # No need to proceed anyfurther
                elif current_command.nid == 'wait':
                    time_to_display = current_command.value
                    if num_frames >= time_to_display:
                        current_command = proceed()
                    else:
                        break
                else:
                    current_command = proceed()

        elif self.paused:
            current_command = self.timeline_menu.get_current_command()
        else:
            current_command = self.timeline_menu.get_first_command_frame()
        return current_command

    def draw_frame(self):
        current_command = self.process()
        if not current_command:
            return

        # Actually show current frame
        if current_command.nid == 'frame':
            frame = current_command.value[1]
            actor_pix = self.modify_for_palette(frame.pixmap)
        elif current_command.nid == 'wait':
            actor_pix = None
        else:
            return
        self.anim_view.set_image(actor_pix)
        self.anim_view.show_image()
