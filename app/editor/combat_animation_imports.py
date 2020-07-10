import os, glob

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QImage, QPixmap, qRgb, QColor, QPainter

from app.resources import combat_anims, combat_commands

import app.editor.utilities as editor_utilities

def update_weapon_anim_pixmap(weapon_anim):
    width_limit = 1200
    left = 0
    heights = []
    max_heights = []
    for frame in weapon_anim.frames:
        width, height = frame.pixmap.width(), frame.pixmap.height()
        if left + width > width_limit:
            max_heights.append(max(heights))
            frame.rect = (0, sum(max_heights), width, height)
            heights = [height]
            left = width
        else:
            frame.rect = (left, sum(max_heights), width, height)
            left += width
            heights.append(height)

    total_width = min(width_limit, sum(frame.rect[2] for frame in weapon_anim.frames))
    total_height = sum(max_heights)
    print(total_width, total_height)
    new_pixmap = QPixmap(total_width, total_height)
    new_pixmap.fill(QColor(editor_utilities.qCOLORKEY))
    painter = QPainter()
    painter.begin(new_pixmap)
    for frame in weapon_anim.frames:
        x, y, width, height = frame.rect
        painter.drawPixmap(x, y, frame.pixmap)
    painter.end()
    weapon_anim.pixmap = new_pixmap

def import_from_lion_throne(current, fn):
    """
    Imports weapon animations from a Lion Throne formatted combat animation script file.

    Parameters
    ----------
    current: CombatAnimation
        Combat animation to install new weapon animation onto
    fn: str, filename
        "*-Script.txt" file to read from
    """

    print(fn)
    kind = os.path.split(fn)[-1].replace('-Script.txt', '')
    print(kind)
    nid, weapon = kind.split('-')
    index_fn = fn.replace('-Script.txt', '-Index.txt')
    if not os.path.exists(index_fn):
        QMessageBox.critical(None, "Error", "Could not find associated index file: %s" % index_fn)
        return
    images = glob.glob(fn.replace('-Script.txt', '-*.png'))
    if not images:
        QMessageBox.critical(None, "Error", "Could not find any associated palettes")
        return
    palette_nids = []
    for image_fn in images:
        palette_nid = os.path.split(image_fn)[-1][:-4].split('-')[-1]
        palette_nids.append(palette_nid)
        if palette_nid not in current.palettes:
            pix = QPixmap(image_fn)
            palette_colors = editor_utilities.find_palette(pix.toImage())
            new_palette = combat_anims.Palette(palette_nid, palette_colors)
            current.palettes.append(new_palette)
    new_weapon = combat_anims.WeaponAnimation(weapon)
    # Now add frames to weapon animation
    with open(index_fn, encoding='utf-8') as index_fp:
        index_lines = [line.strip() for line in index_fp.readlines()]
        index_lines = [l.split(';') for l in index_lines]

    # Use the first palette
    my_colors = current.palettes[0].colors
    base_colors = combat_anims.base_palette.colors
    convert_dict = {qRgb(*a): qRgb(*b) for a, b in zip(my_colors, base_colors)}
    main_pixmap = QPixmap(images[0])
    for i in index_lines:
        nid = i[0]
        x, y = [int(_) for _ in i[1].split(',')]
        width, height = [int(_) for _ in i[2].split(',')]
        offset_x, offset_y = [int(_) for _ in i[3].split(',')]
        new_pixmap = main_pixmap.copy(x, y, width, height)
        # Need to convert to universal base palette
        im = new_pixmap.toImage()
        im.convertTo(QImage.Format_Indexed8)
        im = editor_utilities.color_convert(im, convert_dict)
        new_pixmap = QPixmap.fromImage(im)
        new_frame = combat_anims.Frame(nid, (x, y, width, height), (offset_x, offset_y), pixmap=new_pixmap)
        new_weapon.frames.append(new_frame)

    # Need to build full image file now
    sprite_sheet = QPixmap(main_pixmap.width(), main_pixmap.height())
    sprite_sheet.fill(QColor(editor_utilities.qCOLORKEY))
    painter = QPainter()
    painter.begin(sprite_sheet)
    for frame in new_weapon.frames:
        x, y, width, height = frame.rect
        painter.drawPixmap(x, y, frame.pixmap)
    painter.end()
    new_weapon.pixmap = sprite_sheet

    # Now add poses to the weapon anim
    with open(fn, encoding='utf-8') as script_fp:
        script_lines = [line.strip() for line in script_fp.readlines()]
        script_lines = [line.split(';') for line in script_lines if line and not line.startswith('#')]
    current_pose = None
    for line in script_lines:
        if line[0] == 'pose':
            current_pose = combat_anims.Pose(line[1])
            new_weapon.poses.append(current_pose)
        else:
            command = combat_commands.parse_text(line)
            current_pose.timeline.append(command)
    # Actually add weapon to current
    if new_weapon.nid in current.weapon_anims.keys():
        current.weapon_anims.remove_key(new_weapon.nid)
    current.weapon_anims.append(new_weapon)
    print("Done!!! %s" % fn)
