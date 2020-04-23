from app.constants import COLORKEY
from app.data.resources import RESOURCES

from app.engine import engine, image_mods

def draw_item(surf, item, topleft, effective=False, cooldown=False):
    image = RESOURCES.icons16x16.get(item.icon_nid)
    image = engine.subsurface(image, (item.icon_index[0] * 16, item.icon_index[1] * 16, 16, 16))
    engine.set_colorkey(image, COLORKEY, rleaccel=True)

    if effective:
        image = image_mods.make_white(image.convert_alpha(), abs(250 - engine.get_time()%500)/250) 
    surf.blit(image, topleft)
    return surf
