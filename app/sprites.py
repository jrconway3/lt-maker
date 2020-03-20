import os
from dataclasses import dataclass

@dataclass
class BasicSprite(object):
    full_path: str = None
    pixmap: str = None

def load_sprites(root, files):
    for name in files:
        if name.endswith('.png'):
            full_name = os.path.join(root, name)
            SPRITES[name[:-4]] = BasicSprite(full_name)

SPRITES = {}
for root, dirs, files in os.walk('sprites/'):
    load_sprites(root, files)
