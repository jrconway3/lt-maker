from app.data.resources import RESOURCES
from app.sprites import SPRITES

from app.engine import engine, bmpfont

for sprite in SPRITES.values():
    sprite.image = engine.image_load(sprite.full_path)

FONT = {font.nid.lower(): bmpfont.BmpFont(font.png_path, font.idx_path) for font in RESOURCES.fonts.values()}
