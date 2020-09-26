from app.constants import COLORKEY
from app.resources.resources import RESOURCES

from app.engine import engine

def get_item_icon(item):
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

def draw_weapon(surf, weapon, topleft):
    image = RESOURCES.icons16.get(weapon.icon_nid)
    if not image:
        return surf

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (weapon.icon_index[0] * 16, weapon.icon_index[1] * 16, 16, 16))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)
    
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

def draw_portrait(surf, nid, topleft=None, bottomright=None):
    image = RESOURCES.portraits.get(nid)
    if not image:
        return surf

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (0, 0, 96, 80))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    if topleft:
        surf.blit(image, topleft)
    elif bottomright:
        surf.blit(image, (bottomright[0] - 96, bottomright[1] - 80))
    return surf

def draw_chibi(surf, nid, topleft=None, bottomright=None):
    image = RESOURCES.portraits.get(nid)
    if not image:
        return surf

    if not image.image:
        image.image = engine.image_load(image.full_path)
    image = engine.subsurface(image.image, (96, 16, 32, 32))
    image = image.convert()
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    if topleft:
        surf.blit(image, topleft)
    elif bottomright:
        surf.blit(image, (bottomright[0] - 32, bottomright[1] - 32))
    return surf
