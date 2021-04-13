from app.database.data import DB

from app.utilities import utils

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

    def check_bonus_range(self, unit1, unit2) -> bool:
        return self.check_range(unit1, unit2, 'bonus_range')

    def check_growth_range(self, unit1, unit2) -> bool:
        return self.check_range(unit1, unit2, 'growth_range')

    def check_range(self, unit1, unit2, constant):
        if not unit1.position or not unit2.position:
            return False
        r = DB.support_constants.value(constant)
        if r == 99:
            return True
        elif r == 0:
            return False
        else:
            dist = utils.calculate_distance(unit1.position, unit2.position)
            return dist <= r 

    def get_bonus(self, unit1, unit2, highest_rank):
        pass
        # TODO
