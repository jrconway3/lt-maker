class MapSprite():
    def __init__(self, nid, stand_full_path=None, move_full_path=None, standing_pixmap=None, moving_pixmap=None):
        self.nid = nid
        self.standing_full_path = stand_full_path
        self.moving_full_path = move_full_path
        self.standing_pixmap = standing_pixmap
        self.moving_pixmap = moving_pixmap
        self.standing_image = None
        self.moving_image = None

    def set_standing_full_path(self, full_path):
        self.standing_full_path = full_path

    def set_moving_full_path(self, full_path):
        self.moving_full_path = full_path

    def serialize(self):
        return (self.nid, self.standing_full_path, self.moving_full_path)

    @classmethod
    def deserialize(cls, s_tuple):
        self = cls(*s_tuple)
        return self
