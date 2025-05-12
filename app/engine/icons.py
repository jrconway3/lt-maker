import math

from app.utilities import utils
from app.utilities.enums import HAlignment

from app.constants import COLORKEY
from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine import engine, skill_system, image_mods, unit_funcs

def get_icon_by_name(name) -> engine.Surface:
    image, index = None, None
    for icon_sheet in RESOURCES.icons16:
        if icon_sheet.get_index(name):
            image = icon_sheet
            index = icon_sheet.get_index(name)
    if not image or not index:
        return None
    if not image.image:
        image.image = engine.image_load(image.full_path)
    x, y = index
    image = engine.subsurface(image.image, (x * 16, y * 16, 16, 16))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    return image

def get_icon_by_nid(nid, x, y) -> engine.Surface:
    image = RESOURCES.icons16.get(nid)
    if not image:
        return None
    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (x * 16, y * 16, 16, 16))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    return image

def get_icon(item) -> engine.Surface:
    if not item:
        return None
    image = RESOURCES.icons16.get(item.icon_nid)
    if not image:
        return None

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (item.icon_index[0] * 16, item.icon_index[1] * 16, 16, 16))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    return image

def draw_item(surf, item, topleft, cooldown=False):
    image = get_icon(item)
    if not image:
        return None

    surf.blit(image, topleft)

    return surf

def draw_skill(surf, skill, topleft, compact=True, simple=False, grey=False):
    image = get_icon(skill)
    if not image:
        return None

    if grey:
        image = image_mods.make_gray_colorkey(image)

    surf.blit(image, topleft)
    if simple:
        return surf
    frac = skill_system.get_cooldown(skill)
    if frac is not None and frac < 1:
        cooldown_surf = SPRITES.get('icon_cooldown')
        index = utils.clamp(int(8 * frac), 0, 7)
        c = engine.subsurface(cooldown_surf, (16 * index, 0, 16, 16))
        surf.blit(c, topleft, None, engine.BLEND_RGB_MULT)

    if compact:
        pass
    else:
        text = skill_system.get_text(skill)
        if text is not None:
            FONT['text-blue'].blit(text, surf, (topleft[0] + 16, topleft[1]))

    return surf

def draw_icon_by_alias(surf, icon_alias, topleft):
    image = get_icon_by_name(icon_alias)
    if not image:
        return None
    surf.blit(image, topleft)
    return surf

def draw_weapon(surf, weapon_type, topleft, gray=False):
    w_type_obj = DB.weapons.get(weapon_type)
    if not w_type_obj:
        return surf
    image = RESOURCES.icons16.get(w_type_obj.icon_nid)
    if not image:
        return surf

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (w_type_obj.icon_index[0] * 16, w_type_obj.icon_index[1] * 16, 16, 16))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    if gray:
        image = image_mods.make_gray(image.convert_alpha())

    surf.blit(image, topleft)
    return surf

def draw_faction(surf, faction, topleft):
    image = RESOURCES.icons32.get(faction.icon_nid)
    if not image:
        return surf

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (faction.icon_index[0] * 32, faction.icon_index[1] * 32, 32, 32))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    surf.blit(image, topleft)
    return surf

def get_portrait(unit) -> tuple:
    image = RESOURCES.portraits.get(unit.portrait_nid)
    if image:
        offset = image.info_offset
        if not image.image:
            image.image = engine.image_load(image.full_path)
        image = engine.subsurface(image.image, (0, 0, 96, 80))
    else:  # Generic class portrait
        klass = DB.classes.get(unit.klass)
        image = RESOURCES.icons80.get(klass.icon_nid)
        if not image:
            return None, 0
        if not image.image:
            image.image = engine.image_load(image.full_path)
        image = engine.subsurface(image.image, (klass.icon_index[0] * 80, klass.icon_index[1] * 72, 80, 72))
        offset = 0

    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    return image, offset

def get_portrait_from_nid(portrait_nid) -> tuple:
    image = RESOURCES.portraits.get(portrait_nid)
    if image:
        offset = image.info_offset
        if not image.image:
            image.image = engine.image_load(image.full_path)
        image = engine.subsurface(image.image, (0, 0, 96, 80))
        image = image.convert()
        engine.set_colorkey(image, COLORKEY, rleaccel=True)
    else:
        offset = 0
    return image, offset

def draw_portrait(surf, unit, topleft=None, bottomright=None):
    image, _ = get_portrait(unit)
    if not image:
        return None

    if topleft:
        surf.blit(image, topleft)
    elif bottomright:
        surf.blit(image, (bottomright[0] - 96, bottomright[1] - 80))
    return surf

def get_chibi(portrait):
    if not portrait.image:
        portrait.image = engine.image_load(portrait.full_path)
    image = engine.subsurface(portrait.image, (portrait.image.get_width() - 32, 16, 32, 32))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    return image

def draw_chibi(surf, nid, topleft=None, bottomright=None):
    portrait = RESOURCES.portraits.get(nid)
    if not portrait:
        return surf
    image = get_chibi(portrait)

    if topleft:
        surf.blit(image, topleft)
    elif bottomright:
        surf.blit(image, (bottomright[0] - 32, bottomright[1] - 32))
    return surf

def draw_stat(surf, stat_nid, unit, topright, compact=False):
    if stat_nid not in DB.stats:
        FONT['text-yellow'].blit_right('--', surf, topright)
        return
    value = unit.stats.get(stat_nid, 0)
    bonus = unit.stat_bonus(stat_nid)
    subtle_bonus = unit.subtle_stat_bonus(stat_nid)
    max_stat = unit.get_stat_cap(stat_nid)
    if compact:
        if value >= max_stat:
            draw_glow(surf, FONT['text-green'], str(value + bonus), topright, HAlignment.RIGHT)
            return

        if bonus > 0:
            typeface = FONT['text-green']
        elif bonus < 0:
            typeface = FONT['text-red']
        else:
            typeface = FONT['text-blue']
        typeface.blit_right(str(value + bonus), surf, topright)
    else:
        # Recalc these values for full display
        value = value + subtle_bonus
        bonus = bonus - subtle_bonus
        if value >= max_stat:
            draw_glow(surf, FONT['text-green'], str(value), topright, HAlignment.RIGHT)
        else:
            FONT['text-blue'].blit_right(str(value), surf, topright)
        if bonus > 0:
            draw_glow(surf, FONT['small-green'], "+%d" % bonus, topright)
        elif bonus < 0:
            draw_glow(surf, FONT['small-red'], str(bonus), topright)

def draw_growth(surf, stat_nid, unit, topright, compact=False):
    if stat_nid not in DB.stats:
        FONT['text-yellow'].blit_right('--', surf, topright)
        return
    value = unit_funcs.base_growth_rate(unit, stat_nid)
    value_and_bonus = unit_funcs.growth_rate(unit, stat_nid)
    bonus = value_and_bonus - value
    if compact:
        pass
    else:
        FONT['text-blue'].blit_right(str(value), surf, topright)
        if bonus > 0:
            FONT['small-green'].blit("+%d" % bonus, surf, topright)
        elif bonus < 0:
            FONT['small-red'].blit(str(bonus), surf, topright)

def draw_glow(surf, font, text, topright, align: HAlignment = HAlignment.LEFT):
    interval = 800   # ms
    progress = engine.get_time() % (interval*2)  # Between 0 and 1600
    white = math.sin(progress / interval * math.pi)  # Returns between -1 and 1
    # Rescale to be between 0 and 1
    white = (white + 1) / 2
    
    stat_surf = engine.create_surface(surf.get_size(), True)

    if align == HAlignment.RIGHT:
        font.blit_right(text, stat_surf, topright)
    elif align == HAlignment.CENTER:
        font.blit_center(text, stat_surf, topright)
    else:
        font.blit(text, stat_surf, topright)

    palette = font.font_info.palettes[font.default_color]
    conv_dict = {}
    for idx, color in enumerate(palette):
        if idx == 1:
            continue
        new_color = [min(max(255 * white + rgb, 0), 255) for rgb in color[:3]] + [255]
        conv_dict[tuple(color)] = tuple(new_color)

    image_mods.color_convert_alpha(stat_surf, conv_dict)
    surf.blit(stat_surf, (0, 0))

    return surf
