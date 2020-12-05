from app.utilities.data import Prefab

region_types = ['normal', 'status', 'event', 'formation']

class Region(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.region_type = 'normal'
        self.position = None
        self.size = [1, 1]

        self.sub_nid = None
        self.condition = 'True'
        self.only_once = False

    @property
    def area(self):
        return self.size[0] * self.size[1]

    @property
    def center(self) -> tuple:
        if self.position:
            x = int(self.position[0] + self.size[0] // 2)
            y = int(self.position[1] + self.size[1] // 2)
            return x, y
        else:
            return None
    
    def contains(self, pos: tuple) -> bool:
        x, y = pos
        return self.position[0] <= x < self.position[0] + self.size[0] and \
            self.position[1] <= y < self.position[1] + self.size[1]

    @classmethod
    def default(cls):
        return cls('None')
