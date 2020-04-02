from PyQt5.QtWidgets import QUndoCommand
from PyQt5.QtGui import QPixmap

from app.data.database import DB
from app.data.levels import Level

class CreateNewLevel(QUndoCommand):
    def __init__(self, nid, title):
        self.new_level = Level(nid, title)
        super().__init__("Creating level %s: %s" % (nid, title))

    def undo(self):
        DB.levels.remove(self.new_level)

    def redo(self):
        DB.levels.append(self.new_level)

class ChangeTileTerrain(QUndoCommand):
    def __init__(self, level, pos, new_terrain_nid):
        self.level = level
        self.pos = [pos]
        self.old_terrain = [level.tilemap.tiles[pos].terrain_nid]
        self.new_terrain = [new_terrain_nid]
        super().__init__(
            "(%d, %d): Changed Terrain from %s to %s" % 
            (pos[0], pos[1], self.old_terrain[0], self.new_terrain[0]))
        self.can_merge = True

    def redo(self):
        for pos, new_terrain in zip(self.pos, self.new_terrain):
            self.level.tilemap.tiles[pos].terrain_nid = new_terrain

    def undo(self):
        for pos, old_terrain in zip(self.pos, self.old_terrain):
            self.level.tilemap.tiles[pos].terrain_nid = old_terrain

    def id(self):
        return 0

    def mergeWith(self, other):
        if other.id() != self.id():
            return False
        if not self.can_merge or not other.can_merge:
            return False

        self.pos += other.pos
        self.old_terrain += other.old_terrain
        self.new_terrain += other.new_terrain
        return True

    def makes_change(self):
        return self.old_terrain[0] != self.new_terrain[0]

class ResetTerrain(QUndoCommand):
    def __init__(self, level):
        self.level = level
        self.old_terrain = {}
        tilemap = self.level.tilemap
        for x in range(tilemap.width):
            for y in range(tilemap.height):
                self.old_terrain[(x, y)] = tilemap.tiles[(x, y)].terrain
        super().__init__("Reset all Terrain")

    def redo(self):
        tilemap = self.level.tilemap
        default_terrain = DB.terrain[0]
        for x in range(tilemap.width):
            for y in range(tilemap.height):
                tilemap.tiles[(x, y)].terrain = default_terrain

    def undo(self):
        tilemap = self.level.tilemap
        for x in range(tilemap.width):
            for y in range(tilemap.height):
                tilemap.tiles[(x, y)].terrain = self.old_terrain[(x, y)]

class ChangeTileMapImage(QUndoCommand):
    def __init__(self, level, image_fn):
        self.level = level
        self.new_image = image_fn
        tilemap = self.level.tilemap
        self.old_image = tilemap.base_image
        super().__init__("Changed Tilemap Image to %s" % (image_fn))

    def redo(self):
        im = QPixmap(self.new_image)
        if im:
            self.level.tilemap.change_image(self.new_image, im.width(), im.height())

    def undo(self):
        im = QPixmap(self.old_image)
        if im:
            self.level.tilemap.change_image(self.old_image, im.width(), im.height())
