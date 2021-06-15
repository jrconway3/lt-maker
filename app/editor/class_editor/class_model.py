from PyQt5.QtGui import QIcon, QPixmap, qRgb
from PyQt5.QtCore import Qt

from app.resources.resources import RESOURCES

from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog

from app.editor import timer

from app.editor.custom_widgets import ClassBox
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.map_sprite_editor import map_sprite_model

from app.data import klass

from app.utilities import str_utils
import app.editor.utilities as editor_utilities

def get_map_sprite_icon(klass_obj, num=0, current=False, team='player', variant=None):
    res = None
    if variant:
        res = RESOURCES.map_sprites.get(klass_obj.map_sprite_nid + variant)
    if not variant or not res:
        res = RESOURCES.map_sprites.get(klass_obj.map_sprite_nid)
    if not res:
        return None
    if not res.standing_pixmap:
        res.standing_pixmap = QPixmap(res.stand_full_path)
    pixmap = res.standing_pixmap
    pixmap = map_sprite_model.get_basic_icon(pixmap, num, current, team)
    return pixmap

def get_combat_anim_icon(klass_obj):
    if not klass_obj.combat_anim_nid:
        return None
    combat_anim = RESOURCES.combat_anims.get(klass_obj.combat_anim_nid)
    if not combat_anim or not combat_anim.weapon_anims:
        return None
    weapon_anim = combat_anim.weapon_anims.get('Unarmed', combat_anim.weapon_anims[0])
    pose = weapon_anim.poses.get('Stand')
    if not pose:
        return None

    # Get palette and apply palette
    if not combat_anim.palettes:
        return None
    palette_names = [palette[0] for palette in combat_anim.palettes]
    if 'GenericBlue' in palette_names:
        idx = palette_names.index('GenericBlue')
        palette_name, palette_nid = combat_anim.palettes[idx]
    else:
        palette_name, palette_nid = combat_anim.palettes[0]
    palette = RESOURCES.combat_palettes.get(palette_nid)
    if not palette:
        return None
    colors = palette.colors
    convert_dict = {qRgb(0, coord[0], coord[1]): qRgb(*color) for coord, color in colors.items()}

    # Get first command that displays a frame
    for command in pose.timeline:
        if command.nid in ('frame', 'over_frame', 'under_frame'):
            frame_nid = command.value[1]
            frame = weapon_anim.frames.get(frame_nid)
            if not frame:
                continue
            if not frame.pixmap:
                frame.pixmap = QPixmap(weapon_anim.full_path).copy(*frame.rect)
            pixmap = frame.pixmap
            im = pixmap.toImage()
            im = editor_utilities.color_convert(im, convert_dict)
            im = editor_utilities.convert_colorkey(im)
            pixmap = QPixmap.fromImage(im)
            return pixmap
    return None

class ClassModel(DragDropCollectionModel):
    display_team = 'player'

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            klass = self._data[index.row()]
            text = klass.nid
            return text
        elif role == Qt.DecorationRole:
            klass = self._data[index.row()]
            num = timer.get_timer().passive_counter.count
            if hasattr(self.window, 'view'):
                active = index == self.window.view.currentIndex()
            else:
                active = False
            pixmap = get_map_sprite_icon(klass, num, active, self.display_team)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        return None

    def delete(self, idx):
        # check to make sure nothing else is using me!!!
        klass = self._data[idx]
        nid = klass.nid
        affected_units = [unit for unit in DB.units if unit.klass == nid]
        affected_classes = [k for k in DB.classes if k.promotes_from == nid or nid in k.turns_into]
        affected_ais = [ai for ai in DB.ai if ai.has_unit_spec("Class", nid)]
        affected_levels = [level for level in DB.levels if any(unit.klass == nid for unit in level.units)]
        if affected_units or affected_classes or affected_ais or affected_levels:
            if affected_units:
                affected = Data(affected_units)
                from app.editor.unit_editor.unit_model import UnitModel
                model = UnitModel
            elif affected_classes:
                affected = Data(affected_classes)
                model = ClassModel
            elif affected_ais:
                affected = Data(affected_ais)
                from app.editor.ai_editor.ai_model import AIModel
                model = AIModel
            elif affected_levels:
                affected = Data(affected_levels)
                from app.editor.global_editor.level_menu import LevelModel
                model = LevelModel
            msg = "Deleting Class <b>%s</b> would affect these objects" % nid
            swap, ok = DeletionDialog.get_swap(affected, model, msg, ClassBox(self.window, exclude=klass), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return
        # Delete watchers
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        for unit in DB.units:
            if unit.klass == old_nid:
                unit.klass = new_nid
        for k in DB.classes:
            if k.promotes_from == old_nid:
                k.promotes_from = new_nid
            k.turns_into = [new_nid if elem == old_nid else elem for elem in k.turns_into]
        for ai in DB.ai:
            ai.change_unit_spec("Class", old_nid, new_nid)
        for level in DB.levels:
            for unit in level.units:
                if unit.klass == old_nid:
                    unit.klass = new_nid

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = name = str_utils.get_next_name("New Class", nids)
        movement_group = DB.mcost.unit_types[0]
        bases = {k: 0 for k in DB.stats.keys()}
        growths = {k: 0 for k in DB.stats.keys()}
        growth_bonus = {k: 0 for k in DB.stats.keys()}
        promotion = {k: 0 for k in DB.stats.keys()}
        max_stats = {stat.nid: stat.maximum for stat in DB.stats}
        wexp_gain = {weapon_nid: DB.weapons.default() for weapon_nid in DB.weapons.keys()}
        new_class = klass.Klass(
            nid, name, "", 1, movement_group, None, [], [], 20,
            bases, growths, growth_bonus, promotion, max_stats, 
            [], wexp_gain)
        DB.classes.append(new_class)
        return new_class
