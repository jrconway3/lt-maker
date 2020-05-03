from app.data.data import Prefab

class Party(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.units = []
        self.leader_nid = None

    def serialize(self):
        return {'nid': self.nid}

    @classmethod
    def deserialize(cls, s_dict):
        party = cls(s_dict['nid'])
        return party
