import glob
from counters import OrderedDict
from functools import reduce

from PyQt5.QtGui import QImage

from app.constants import TILEWIDTH, TILEHEIGHT

AUTOTILE_FRAMES = 16

def similar(p1, p2):
    return sum(i != j for i, j in zip(p1, p2))

def similar_fast(p1, p2):
    return 0 if p1 == p2 else TILEWIDTH * TILEHEIGHT

class Series(list):
    def is_present(self, test) -> bool:
        test_palette = test.palette
        all_palettes = [im.palette for im in self]
        for palette in all_palettes:
            if similar(test_palette, palette):
                return True
        return False

    def is_present_fast(self, test) -> bool:
        test_palette = test.palette
        all_palettes = [im.palette for im in self]
        for palette in all_palettes:
            if similar_fast(test_palette, palette, False):
                return True
        return False

    def is_present_slow(self, test) -> bool:
        return test.palette in [im.palette for im in self]

    def get_frames_with_color(self, color) -> list:
        return [im for im in self if color in im.colors]

class PaletteData():
    def __init__(self, arr):
        self.arr = arr
        self.colors = list(arr.getdata())
        self.uniques = reduce(lambda l, x: l if x in l else l + [x], self.colors, [])
        # Sort by most popular
        self.uniques = sorted(self.uniques, key=lambda x: self.colors.count(x), reverse=True)
        self.palette = self.colors[:]

        for idx, pixel in enumerate(self.colors):
            # Each pixel in the palette is assigned its color id
            self.palette[idx] = self.uniques.index(pixel)

class AutotileMaker():
    def __init__(self, tileset):
        self.tileset = tileset
        self.tileset_image = QImage(self.tileset.pixmap)

        self.running = True
        self.now_an_autotile = []

        self.autotile_templates = self.gather_templates()
        self.books = []

    def gather_templates(self):
        templates = []
        for fn in sorted(glob.glob('resources/autotiles/*.png')):
            templates.append(fn)
        return templates

    def load_autotile_templates(self):
        # Each autotile template becomes a book
        # A book contains a dictionary
        # Key: position
        # Value: Series
        for template in self.autotile_templates:
            image = QImage.open(template)
            width = image.width // AUTOTILE_FRAMES
            height = image.height
            num_tiles_x = width // TILEWIDTH
            num_tiles_y = height // TILEHEIGHT
            num = num_tiles_x * num_tiles_y
            minitiles = [Series() for _ in range(num)]

            # There are 16 frames, stacked horizontally with one another
            for frame in range(AUTOTILE_FRAMES):
                x_offset = frame * width
                for x in range(num_tiles_x):
                    for y in range(num_tiles_y):
                        rect = (x_offset + x * TILEWIDTH, y * TILEHEIGHT, x_offset + x * TILEWIDTH + TILEWIDTH, y * TILEHEIGHT + TILEHEIGHT)
                        palette = image.crop(rect)
                        minitiles[x + y * num_tiles_x].append(PaletteData(palette))

            assert all(len(series.series) == AUTOTILE_FRAMES for series in minitiles)
            self.books.append(minitiles)

    def comparison(self):
        """
        Generates map tiles
        """
        self.map_tiles = OrderedDict()

        for x in range(self.tileset.width // TILEWIDTH):
            for y in range(self.tileset.height // TILEHEIGHT):
                rect = (x * TILEWIDTH, y * TILEHEIGHT, x * TILEWIDTH + TILEWIDTH, y * TILEHEIGHT + TILEHEIGHT)
                tile = self.tileset_image.crop(rect)
                tile_palette = PaletteData(tile)
                self.map_tiles[(x, y)] = tile_palette

    def create_autotiles_from_image(self, pos):
        x, y = pos
        tile_palette = self.map_tiles[(x, y)]

        closest_series = None
        closest_frame = None
        closest_book = None
        min_sim = 16

        for book_idx, book in enumerate(self.books):
            for series_idx, series in enumerate(book):
                for frame_idx, frame in enumerate(series):
                    similarity = similar_fast(frame.palette, tile_palette.palette)
                    if similarity < min_sim:
                        min_sim = similarity
                        closest_series = series
                        closest_frame = frame
                        closest_book = book

        if closest_series:
            self.color_change_band(closest_book, closest_series, closest_frame, tile_palette, (x, y))
            self.now_an_autotile.append((x, y))

    def color_change_band(self, closest_book, closest_series, closest_frame, tile, pos):
        """
        Changes the color of a band to match palette color of the original tileset
        """
        x, y = pos
        # Converts color from closest frame to tile
        color_conversion = {}
        for idx, color in enumerate(closest_frame.colors):
            color_conversion[color] = tile.colors[idx]

        # What colors are missing?
        def fix_missing_color(color):
            # Does that color show up in other frames in the autotile band?
            for series in closest_book:
                frames_with_color = series.get_frames_with_color(color)
                for f in frames_with_color:
                    for map_tile in self.map_tiles.values():
                        # If so, do those frames show up in the map sprite?
                        if similar_fast(f.palette, map_tile.palette):
                            # If so, add the color conversion
                            color_idx = f.colors.idx(color)
                            new_color = map_tile.colors[color_idx]
                            color_conversion[color] = new_color
                            print("%s has become %s" % (color, new_color))
                            return

        for band in range(AUTOTILE_FRAMES):
            for idx, color in enumerate(closest_series[band].colors):
                if color not in color_conversion:
                    print("Missing Color: %s" % str(color))
                    fix_missing_color(color)

        # Now actually build new images
        height = AUTOTILE_FRAMES * TILEHEIGHT
        width = TILEWIDTH

