from app.utilities.data import Prefab

region_types = ['Normal', 'Status', 'Event', 'Formation']

class Region(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.region_type = 'Normal'
        self.position = None
        self.size = [1, 1]

        self.sub_nid = None
        self.condition = 'True'

    @classmethod
    def default(cls):
        return cls('None')
