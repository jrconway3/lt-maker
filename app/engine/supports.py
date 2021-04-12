from app.database.data import DB

class SupportPair():
    """
    Keeps track of necessary values for each support pair
    """
    def __init__(self, nid):
        self.nid = nid
        self.points = 0
        self.unlocked_ranks = []

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['points'] = self.points
        s_dict['unlocked_ranks'] = self.unlocked_ranks

    @classmethod
    def restore(cls, s_dict):
        obj = cls(s_dict['nid'])
        obj.points = int(s_dict['points'])
        obj.unlocked_ranks = s_dict['unlocked_ranks']

class SupportController():
    def __init__(self):
        self.support_pairs = {}

    def get_pairs(self, unit_nid: str) -> list:
        pairs = []
        for key, pair in self.support_pairs.items():
            prefab = DB.support_pairs.get(key)
            if prefab.unit1 == unit_nid or (prefab.unit2 == unit_nid and not prefab.one_way):
                pairs.append(pair)
        return pairs
