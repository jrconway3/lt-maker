from app.utilities.data import Prefab

class PartyObject(Prefab):
    def __init__(self, nid, name, leader_nid, units=None, money=0, convoy=None, bexp=0):
        self.nid = nid
        self.name = name
        self.leader_nid = leader_nid
        self.units = units or []  # Unit nids
        self.money = money
        self.convoy = convoy or []
        self.bexp = bexp

    def save(self):
        return {'nid': self.nid, 
                'name': self.name, 
                'leader_nid': self.leader_nid,
                'units': self.units,
                'money': self.money,
                'convoy': self.convoy,
                'bexp': self.bexp}

    @classmethod
    def restore(cls, s_dict):
        party = cls(s_dict['nid'], s_dict['name'], s_dict['leader_nid'], s_dict['units'], s_dict['money'], s_dict['convoy'], s_dict['bexp'])
        return party
