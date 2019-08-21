import os

def get_sprites(home):
    s = {}
    for root, dirs, files in os.walk(home):
        for name in files:
            if name.endswith('.png'):
                full_name = os.path.join(root, name)
                s[name[:-4]] = full_name
    return s

SPRITES = get_sprites('./sprites/')
