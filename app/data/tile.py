class Tile(object):
    def __init__(self, terrain, position, parent):
        self.parent = parent
        self.terrain = terrain
        self.position = position

        self.current_hp = 0
