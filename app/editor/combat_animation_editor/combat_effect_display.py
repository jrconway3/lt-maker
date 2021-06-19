import os

from PyQt5.QtWidgets import QVBoxLayout, \
    QWidget, QGroupBox, QFormLayout, QFileDialog, \
    QPushButton, QLineEdit, QInputDialog
from PyQt5.QtGui import QImage, QPixmap, QPainter

from app.constants import WINWIDTH, WINHEIGHT
from app.resources import combat_anims
from app.resources.resources import RESOURCES
from app.data.database import DB

from app.editor.settings import MainSettingsController

from app.editor import timer

from app.editor.combat_animation_editor.frame_selector import FrameSelector
from app.editor.combat_animation_editor.combat_animation_display import CombatAnimProperties
import app.editor.combat_animation_editor.combat_animation_imports as combat_animation_imports

import app.editor.utilities as editor_utilities
from app.utilities import str_utils

# Game interface
import app.editor.game_actions.game_actions as GAME_ACTIONS

class CombatEffectProperties(CombatAnimProperties):
    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data

        # Populate resources
        for effect_anim in self._data:
            effect_anim.pixmap = QPixmap(effect_anim.full_path)
            for frame in effect_anim.frames:
                x, y, width, height = frame.rect
                frame.pixmap = effect_anim.pixmap.copy(x, y, width, height)

        self.control_setup(current)
        self.test_combat_button.setEnabled(False)

        self.info_form = QFormLayout()

        self.nid_box = QLineEdit()
        self.nid_box.textChanged.connect(self.nid_changed)
        self.nid_box.editingFinished.connect(self.nid_done_editing)

        self.settings = MainSettingsController()
        theme = self.settings.get_theme(0)
        if theme == 0:
            icon_folder = 'icons/icons'
        else:
            icon_folder = 'icons/dark_icons'

        pose_row = self.pose_box(icon_folder)

        self.info_form.addRow("Unique ID", self.nid_box)
        self.info_form.addRow("Pose", pose_row)

        self.build_frames()
        self.set_layout()

    def on_nid_changed(self, old_nid, new_nid):
        pass

    def build_frames(self):
        self.frame_group_box = QGroupBox()
        self.frame_group_box.setTitle("Image Frames")
        frame_layout = QVBoxLayout()
        self.frame_group_box.setLayout(frame_layout)
        self.import_from_lt_button = QPushButton("Import Legacy Effect...")
        self.import_from_lt_button.clicked.connect(self.import_legacy)
        self.import_png_button = QPushButton("View Frames...")
        self.import_png_button.clicked.connect(self.select_frame)
        self.window.left_frame.layout().addWidget(self.import_from_lt_button, 2, 0, 1, 2)
        frame_layout.addWidget(self.import_png_button)

    def pose_changed(self, idx):
        current_pose_nid = self.pose_box.currentText()
        poses = self.current.poses
        current_pose = poses.get(current_pose_nid)
        if current_pose:
            self.has_pose(True)
            self.timeline_menu.set_current_pose(current_pose)
        else:
            self.has_pose(False)
            self.timeline_menu.clear_pose()

    def get_available_pose_types(self) -> float:
        items = [_ for _ in combat_anims.required_poses] + ['Critical']
        items.append("Custom")
        for pose_nid in self.current.poses.keys():
            if pose_nid in items:
                items.remove(pose_nid)
        return items

    def make_pose(self):
        items = self.get_available_pose_types()

        new_nid, ok = QInputDialog.getItem(self, "New Pose", "Select Pose", items, 0, False)
        if not new_nid or not ok:
            return
        if new_nid == "Custom":
            new_nid, ok = QInputDialog.getText(self, "Custom Pose", "Enter New Name for Pose: ")
            if not new_nid or not ok:
                return
            new_nid = str_utils.get_next_name(new_nid, self.current.poses.keys())
        return new_nid

    def add_new_pose(self):
        new_nid = self.make_pose()
        if not new_nid:
            return
        
        new_pose = combat_anims.Pose(new_nid)
        self.current.poses.append(new_pose)
        self.pose_box.addItem(new_nid)
        self.pose_box.setValue(new_nid)

    def duplicate_pose(self):
        new_nid = self.make_pose()
        if not new_nid:
            return 

        current_pose_nid = self.pose_box.currentText()
        current_pose = self.current.poses.get(current_pose_nid)
        # Make a copy
        ser = current_pose.serialize()
        new_pose = combat_anims.Pose.deserialize(ser)
        new_pose.nid = new_nid
        self.current.poses.append(new_pose)
        self.pose_box.addItem(new_nid)
        self.pose_box.setValue(new_nid)
        return new_pose

    def delete_pose(self):
        pose = self.current.poses.get(self.pose_box.currentText())
        if self.ask_permission(pose, 'Pose'):
            self.current.poses.delete(pose)
            self.reset_pose_box()

    def reset_pose_box(self):
        self.pose_box.clear()
        poses = self.current.poses
        if poses:
            self.pose_box.addItems([d.nid for d in poses])
            self.pose_box.setValue(poses[0].nid)
        return poses

    def import_legacy(self):
        starting_path = self.settings.get_last_open_path()
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Legacy Effect Script Files", starting_path, "Script Files (*-Script.txt);;All Files (*)")
        if ok and fns:
            for fn in fns:
                if fn.endswith('-Script.txt'):
                    combat_animation_imports.import_effect_from_legacy(fn)
            parent_dir = os.path.split(fns[-1])[0]
            self.settings.set_last_open_path(parent_dir)
        self.window.update_list()

    def select_frame(self):
        dlg = FrameSelector(self.current, self.current, self)
        dlg.exec_()

    def set_current(self, current):
        self.stop()

        self.current = current
        self.nid_box.setText(self.current.nid)

        poses = self.reset_pose_box()
        self.timeline_menu.set_current_frames(self.current.frames)
        self.palette_menu.set_current(self.current)
        current_pose_nid = self.pose_box.currentText()
        current_pose = poses.get(current_pose_nid)
        if current_pose:
            self.timeline_menu.set_current_pose(current_pose)
        else:
            self.timeline_menu.clear_pose()

    def draw_frame(self):
        self.update()

        # Actually show current frame
        # Need to draw 240x160 area
        # And place in space according to offset
        actor_im = None
        offset_x, offset_y = 0, 0
        under_actor_im = None
        under_offset_x, under_offset_y = 0, 0

        if self.frame_nid:
            frame = self.current.frames.get(self.frame_nid)
            if frame:
                if self.custom_frame_offset:
                    offset_x, offset_y = self.custom_frame_offset
                else:
                    offset_x, offset_y = frame.offset
                actor_im = self.modify_for_palette(frame.pixmap)
        if self.under_frame_nid:
            frame = self.current.frames.get(self.under_frame_nid)
            if frame:
                under_offset_x, under_offset_y = frame.offset
                under_actor_im = self.modify_for_palette(frame.pixmap)

        self.set_anim_view(actor_im, (offset_x, offset_y), under_actor_im, (under_offset_x, under_offset_y))

    def export(self, fn_dir: str):
        current_pose_nid = self.pose_box.currentText()
        current_pose = self.current.poses.get(current_pose_nid)
        counter = 0
        for command in current_pose.timeline:
            self.processing = True
            self.do_command(command)
            if self.processing:  # Don't bother drawing anything if we are still processing
                continue
            im = QImage(WINWIDTH, WINHEIGHT, QImage.Format_ARGB32)
            im.fill(editor_utilities.qCOLORKEY)
            frame, under_frame = None, None
            if self.under_frame_nid:
                under_frame = self.current.frames.get(self.under_frame_nid)
                under_offset_x, under_offset_y = under_frame.offset
                under_frame = self.modify_for_palette(under_frame.pixmap)
            if self.frame_nid:
                frame = self.current.frames.get(self.frame_nid)
                if self.custom_frame_offset:
                    offset_x, offset_y = self.custom_frame_offset
                else:
                    offset_x, offset_y = frame.offset
                frame = self.modify_for_palette(frame.pixmap)
            if frame or under_frame:
                painter = QPainter()
                painter.begin(im)
                if under_frame:
                    painter.drawImage(under_offset_x, under_offset_y, under_frame)
                if frame:
                    painter.drawImage(offset_x, offset_y, frame)
                painter.end()
            for i in range(self.num_frames):
                path = '%s_%s_%04d.png' % (self.current.nid, current_pose.nid, counter)
                full_path = os.path.join(fn_dir, path)
                im.save(full_path)
                counter += 1

    def find_appropriate_combat_anim(self, pose_nid: str) -> tuple:
        for combat_anim in RESOURCES.combat_anims:
            for weapon_anim in combat_anim.weapon_anims:
                pose = weapon_anim.poses.get(pose_nid)
                if pose:
                    for command in pose.timeline:
                        if command.nid == 'spell' and command.value[0] is None:
                            return combat_anim, weapon_anim
        return None, None

    def test_combat(self):
        if self.current:
            current_pose_nid = self.pose_box.currentText()
            if 'Attack' in self.current.poses.keys():
                pass
            else:
                print("Missing Attack pose!")
                return

            # Find a combat animation with this pose and "spell empty" in it's pose
            combat_anim, weapon_anim = self.find_appropriate_combat_anim(current_pose_nid)
            if not weapon_anim:
                print("Couldn't find a usable weapon anim")
                return None

            left_palette, right_palette = self.get_test_palettes(combat_anim)
            
            timer.get_timer().stop()
            GAME_ACTIONS.test_combat(
                weapon_anim, left_palette, self.current.nid, 
                weapon_anim, right_palette, self.current.nid, current_pose_nid)
            timer.get_timer().start()
