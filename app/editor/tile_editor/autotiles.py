import glob
from counters import OrderedDict

from PyQt5.QtGui import QImage, QColor

from app.editor import utilities as editor_utilities

from app.constants import TILEWIDTH, TILEHEIGHT

AUTOTILE_FRAMES = 16

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

    def get_frames_with_color(self, color: QColor) -> list:
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
    def __init__(self, tileset):
        self.tileset = tileset
        self.tileset_image = QImage(self.tileset.pixmap)

        self.books = []
        self.autotile_column_idxs = {}
        self.recognized_series = []
        self.companion_autotile_im = None

        self.autotile_templates = self.gather_templates()
        self.load_autotile_templates()
        self.palettize_tileset()

        for pos in self.map_tiles:
            self.create_autotiles_from_image(pos)

        if self.recognized_series:
            self.create_final_image()
        final_column_idxs = {k: v[0] for k, v in self.autotile_templates.items()}
        return self.companion_autotile_im, final_column_idxs

    def gather_templates(self) -> list:
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
            print(template)
            image = QImage.open(template)
            width = image.width() // AUTOTILE_FRAMES
            height = image.height()
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
                        palette = image.copy(*rect)  # crop
                        d = PaletteData(palette)
                        minitiles[x + y * num_tiles_x].append(d)

            assert all(len(series.series) == AUTOTILE_FRAMES for series in minitiles)
            self.books.append(minitiles)

    def palettize_tileset(self):
        """
        Generates map tiles
        """
        self.map_tiles = OrderedDict()

        for x in range(self.tileset.width // TILEWIDTH):
            for y in range(self.tileset.height // TILEHEIGHT):
                rect = (x * TILEWIDTH, y * TILEHEIGHT, x * TILEWIDTH + TILEWIDTH, y * TILEHEIGHT + TILEHEIGHT)
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
                        print(pos)

        if closest_series:
            if closest_series in self.recognized_series:
                column_idx = self.recognized_series.index(closest_series)
            else:
                # Add series to autotile column list if it is not already
                # If it's not added to autotile column image, make sure it uses the right colors
                self.recognized_series.append(closest_series)
                column_idx = len(self.recognized_series) - 1
            self.autotile_column_idxs[(x, y)] = (column_idx, closest_frame, closest_series, closest_book)

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
                        if similar(f.palette, map_tile.palette):
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

    def create_final_image(self):
        width = len(self.recognized_series) * TILEWIDTH
        height = AUTOTILE_FRAMES * TILEHEIGHT
        new_im = QImage((width, height))

        painter = QPainter(new_im)
        for i, series in enumerate(self.recognized_series):
            for j, palette_data in series:
                x, y = i * TILEWIDTH, j * TILEHEIGHT
                # Paste image
                painter.drawImage((x, y), palette_data.im)
        painter.end()

        self.companion_autotile_im = new_im
