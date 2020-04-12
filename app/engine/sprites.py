from app.sprites import SPRITES

from app.engine import engine

for sprite in SPRITES.values():
    sprite.pixmap = engine.image_load(sprite.full_path)
