from app.data import tilemap

class Level(object):
    def __init__(self, nid, title):
        self.nid = nid
        self.title = title
        self.tilemap = tilemap.TileMap.default()
