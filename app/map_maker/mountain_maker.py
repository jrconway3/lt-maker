import glob

from PyQt5.QtGui import QImage

from app.editor.tile_editor.autotiles import similar, similar_fast, PaletteData

from app.constants import TILEWIDTH, TILEHEIGHT

def get_mountain_coords(fn) -> set:
    if fn.endswith('rainlash_fields1.png'):
        topleft = {(0, 11), (0, 12), (1, 11), (1, 12), (2, 12), (3, 11), (3, 12)}
        main = {(x, y) for x in range(17) for y in range(13, 20)}
        right = {(17, 14), (17, 15), (17, 16), (17, 17), (17, 18), (17, 19), (18, 16), (18, 17), (18, 18), (18, 19)}
        bottomleft = {(4, 22), (5, 22), (1, 26), (2, 27), (3, 27)}
        bottom = {(x, y) for x in range(6, 12) for y in range(20, 25)}
        bottomright = {(13, 22), (14, 22), (15, 22), (16, 22), (13, 23), (14, 23), (15, 23), (16, 23), (17, 23), (13, 24), (14, 24), (14, 25), (15, 20), (16, 20), (17, 20), (18, 20), (17, 21), (18, 21)}
        return topleft | main | right | bottomleft | bottom | bottomright
    return set()

class MountainPaletteData(PaletteData):
    def __init__(self, im: QImage, coord: tuple):
        super().__init__(im)
        self.coord = coord
        self.rules = {}
        self.rules['left'] = set()
        self.rules['right'] = set()
        self.rules['up'] = set()
        self.rules['down'] = set()

def load_mountain_palettes(fn, coords) -> dict:
    palettes = {}
    image = QImage(fn)
    for coord in coords:
        rect = (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
        palette = image.copy(*rect)
        d = MountainPaletteData(palette, coord)
        palettes[coord] = d
    return palettes

def assign_rules(palette_templates: dict, fns: list):
    print("Assign Rules")
    for fn in fns:
        print(fn)
        image = QImage(fn)
        num_tiles_x = image.width() // TILEWIDTH
        num_tiles_y = image.height() // TILEHEIGHT
        image_palette_data = {}
        for x in range(num_tiles_x):
            for y in range(num_tiles_y):
                rect = (x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                palette = image.copy(*rect)
                d = PaletteData(palette)
                image_palette_data[(x, y)] = d
        
        for position, palette in image_palette_data.items():
            mountain_match = is_present(palette, palette_templates)
            if mountain_match:
                # Find adjacent positions
                left = position[0] - 1, position[1]
                right = position[0] + 1, position[1]
                up = position[0], position[1] - 1
                down = position[0], position[1] + 1
                left_palette = image_palette_data.get(left)
                right_palette = image_palette_data.get(right)
                up_palette = image_palette_data.get(up)
                down_palette = image_palette_data.get(down)
                # determine if those positions are in palette_templates
                # If they are, mark those coordinates in the list of valid coords
                # If not, mark as end validity
                if left_palette:
                    new_mountain = is_present(left_palette, palette_templates)
                    if new_mountain:
                        mountain_match.left_rule.add(new_mountain.coord)
                    else:
                        mountain_match.left_rule.add(None)
                if right_palette:
                    new_mountain = is_present(right_palette, palette_templates)
                    if new_mountain:
                        mountain_match.right_rule.add(new_mountain.coord)
                    else:
                        mountain_match.right_rule.add(None)
                if up_palette:
                    new_mountain = is_present(up_palette, palette_templates)
                    if new_mountain:
                        mountain_match.up_rule.add(new_mountain.coord)
                    else:
                        mountain_match.up_rule.add(None)
                if down_palette:
                    new_mountain = is_present(down_palette, palette_templates)
                    if new_mountain:
                        mountain_match.down_rule.add(new_mountain.coord)
                    else:
                        mountain_match.down_rule.add(None)

def is_present(palette: PaletteData, palette_templates: dict) -> MountainPaletteData:
    for coord, mountain in palette_templates.items():
        if similar_fast(palette.palette, mountain.palette):
            return mountain
    return None

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    tileset = 'app/map_maker/rainlash_fields1.png'
    mountain_coords = get_mountain_coords(tileset)

    mountain_palettes = load_mountain_palettes(tileset, mountain_coords)
    mountain_data_dir = glob.glob('~/Pictures/Fire Emblem/MapReferences/custom_mountain_data/*.png')
    # Stores rules in the palette data itself
    assign_rules(mountain_palettes, mountain_data_dir)

    print("--- Final Rules ---")
    for coord, mountain_palette in mountain_palettes.items():
        print(coord, mountain_palette.rules)
