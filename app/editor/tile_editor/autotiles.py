import glob
from collections import OrderedDict

from PyQt5.QtGui import QImage, QColor, QPainter, qRgb, qRgba

from app.editor import utilities as editor_utilities

from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FRAMES

def similar(p1, p2):
    def similar(p1, p2):
        return sum(i != j for i, j in zip(p1, p2))

    def similar_fast(p1, p2):
        return 0 if p1 == p2 else TILEWIDTH * TILEHEIGHT

    return similar_fast(p1, p2)

class Series(list):
    def is_present(self, test) -> bool:
        test_palette = test.palette
        all_palettes = [im.palette for im in self]
        return any(similar(test_palette, palette) for palette in all_palettes)

    def get_frames_with_color(self, color: tuple) -> list:
        return [im for im in self if color in im.colors]

class PaletteData():
    def __init__(self, im: QImage):
        self.im: QImage = im
        self.colors: list = editor_utilities.get_full_palette(im)
        # Sort by most
        self.uniques: list = sorted(set(self.colors), key=lambda x: self.colors.count(x), reverse=True)
        self.palette: list = self.colors[:]

        for idx, pixel in enumerate(self.colors):
            # Each pixel in the palette is assigned its color id
            self.palette[idx] = self.uniques.index(pixel)
            # So palette is a unique string of ints

class AutotileMaker():
    def __init__(self):
        self.books = []
        self.autotile_column_idxs = {}
        self.recognized_series = []
        self.companion_autotile_im = None

        self.autotile_templates = self.gather_templates()
        self.load_autotile_templates()

    def run(self, tileset):
        self.tileset = tileset
        self.tileset_image = QImage(self.tileset.pixmap)
        self.palettize_tileset()

        for pos in self.map_tiles:
            self.create_autotiles_from_image(pos)

        if self.recognized_series:
            self.create_final_image()

        final_column_idxs = {k: v[0] for k, v in self.autotile_column_idxs.items()}
        return self.companion_autotile_im, final_column_idxs

    def gather_templates(self) -> list:
        templates = []
        for fn in sorted(glob.glob('resources/autotiles/*.png')):
            templates.append(fn)
        return templates

    def load_autotile_templates(self):
        import time
        # Each autotile template becomes a book
        # A book contains a dictionary
        # Key: position
        # Value: Series
        for template in self.autotile_templates:
            print(template)
            image = QImage(template)
            width = image.width() // AUTOTILE_FRAMES
            height = image.height()
            num_tiles_x = width // TILEWIDTH
            num_tiles_y = height // TILEHEIGHT
            num = num_tiles_x * num_tiles_y
            minitiles = [Series() for _ in range(num)]

            # There are 16 frames, stacked horizontally with one another
            time1 = time.time_ns() / 1e6
            for frame in range(AUTOTILE_FRAMES):    
                x_offset = frame * width
                for x in range(num_tiles_x):
                    for y in range(num_tiles_y):
                        rect = (x_offset + x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                        palette = image.copy(*rect)  # crop
                        d = PaletteData(palette)
                        minitiles[x + y * num_tiles_x].append(d)
            time2 = time.time_ns() / 1e6
            print(time2 - time1)

            assert all(len(series) == AUTOTILE_FRAMES for series in minitiles)
            self.books.append(minitiles)

    def palettize_tileset(self):
        """
        Generates map tiles
        """
        self.map_tiles = OrderedDict()
        print("Palettizing current tileset...")

        for x in range(self.tileset.width):
            for y in range(self.tileset.height):
                rect = (x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
                tile = self.tileset_image.copy(*rect)  # Crop
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
                    similarity = similar(frame.palette, tile_palette.palette)
                    if similarity < min_sim:
                        min_sim = similarity
                        closest_series = series
                        closest_frame = frame
                        closest_book = book
                        print("Similarity met for ", pos, book_idx, series_idx, frame_idx)

        if closest_series:
            if closest_series in self.recognized_series:
                column_idx = self.recognized_series.index(closest_series)
            else:
                # Add series to autotile column list if it is not already
                # If it's not added to autotile column image, make sure it uses the right colors
                self.recognized_series.append(closest_series)
                column_idx = len(self.recognized_series) - 1
                self.color_change(tile_palette, closest_frame, closest_series, closest_book)
            print("Final column idx", column_idx)
            self.autotile_column_idxs[(x, y)] = (column_idx, closest_frame, closest_series, closest_book)

    def color_change(self, tile, closest_frame, closest_series, closest_book):
        # Converts color from closest frame to tile
        color_conversion = {}
        truecolor = {}
        for idx, color in enumerate(closest_frame.colors):
            truecolor[color] = tile.colors[idx]
            color_conversion[qRgb(*color)] = qRgb(*tile.colors[idx])

        def fix_missing_color(color: tuple):
            # Does that color show up in other frames in the autotile band?
            for series in closest_book:
                frames_with_color = series.get_frames_with_color(color)
                for f in frames_with_color:
                    for map_tile in self.map_tiles.values():
                        # If so, do those frames show up in the map sprite?
                        if similar(f.palette, map_tile.palette):
                            # If so, add to the color conversion
                            color_idx = f.colors.index(color)
                            new_color = map_tile.colors[color_idx]
                            truecolor[color] = new_color
                            color_conversion[qRgb(*color)] = qRgb(*new_color)
                            print("%s has become %s" % (color, new_color))
                            return

        for palette_data in closest_series:
            for idx, color in enumerate(palette_data.colors):
                if color not in truecolor:
                    print("Missing color: %s" % str(color))
                    fix_missing_color(color)

        for palette_data in closest_series:
            new_im = editor_utilities.color_convert(palette_data.im, color_conversion)
            palette_data.im = new_im

    def create_final_image(self):
        width = len(self.recognized_series) * TILEWIDTH
        height = AUTOTILE_FRAMES * TILEHEIGHT
        new_im = QImage(width, height, QImage.Format_ARGB32)

        painter = QPainter(new_im)
        for i, series in enumerate(self.recognized_series):
            for j, palette_data in enumerate(series):
                x, y = i * TILEWIDTH, j * TILEHEIGHT
                # Paste image
                painter.drawImage(x, y, palette_data.im)
        painter.end()

        self.companion_autotile_im = new_im

AUTOTILEMAKER = None
def get_maker():
    global AUTOTILEMAKER
    if not AUTOTILEMAKER:
        AUTOTILEMAKER = AutotileMaker()
    return AUTOTILEMAKER
