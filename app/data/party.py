from app.data.data import Data, Prefab

from app import utilities

class PartyPrefab(Prefab):
    nid: str = None
    name: str = None
    leader: str = None

class PartyCatalog(Data):
    datatype = PartyPrefab

    def add_new_default(self, db):
        new_row_nid = utilities.get_next_name('New Party', self.keys())
        new_party = PartyPrefab(new_row_nid, "Party Name", None)
        self.append(new_party)
        return new_party

class PartyObject(Prefab):
    def __init__(self, nid, name, leader_nid, units=None):
        self.nid = nid
        self.name = name
        self.leader_nid = leader_nid
        self.units = units or []  # Unit nids
        self.money = 0
        self.convoy = []
        self.bexp = 0

    def serialize(self):
        return {'nid': self.nid, 
                'name': self.name, 
                'leader_nid': self.leader_nid,
                'units': self.units,
                'money': self.money,
                'convoy': self.convoy,
                'bexp': self.bexp}

    @classmethod
    def deserialize(cls, s_dict):
        party = cls(s_dict['nid'], s_dict['name'], s_dict['leader_nid'], s_dict['units'], s_dict['money'], s_dict['convoy'], s_dict['bexp'])
        return party
