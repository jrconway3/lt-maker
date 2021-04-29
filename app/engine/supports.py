from dataclasses import dataclass

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
        return obj

@dataclass
class SupportEffect():
    damage: float = 0
    resist: float = 0
    accuracy: float = 0
    avoid: float = 0
    crit: float = 0
    dodge: float = 0
    attack_speed: float = 0
    defense_speed: float = 0

    def add_effect(self, effect: list):
        self.damage += effect[0]
        self.resist += effect[1]
        self.accuracy += effect[2]
        self.avoid += effect[3]
        self.crit += effect[4]
        self.dodge += effect[5]
        self.attack_speed += effect[6]
        self.defense_speed += effect[7]


class SupportController():
    def __init__(self):
        self.support_pairs = {}

    def save(self):
        return [support_pair.save() for support_pair in self.support_pairs]

    @classmethod
    def restore(cls, s_list):
        self = cls()
        for support_pair_dat in s_list:
            support_pair = SupportPair.restore(support_pair_dat)
            self.support_pairs[support_pair.nid] = support_pair
        return self

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

    def check_range(self, unit1, unit2, constant) -> bool:
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

    def get_specific_bonus(self, unit1, unit2, highest_rank):
        for pair in DB.support_pairs:
            if (pair.unit1 == unit1.nid and pair.unit2 == unit2.nid) or (pair.unit1 == unit2.nid and pair.unit2 == unit1.nid):
                for support_rank_req in pair.requirements:
                    if support_rank_req.support_rank == highest_rank:
                        return support_rank_req
        return None

    def get_bonus(self, unit1, unit2, highest_rank) -> SupportEffect:
        # Get bonus to stats from affinity
        aff1_nid = unit1.affinity
        aff2_nid = unit2.affinity
        aff1 = DB.affinities.get(aff1_nid)
        aff2 = DB.affinities.get(aff2_nid)
        aff1_bonus = None
        aff2_bonus = None
        for support_rank_bonus in aff1.bonus:
            if support_rank_bonus.support_rank == highest_rank:
                aff1_bonus = support_rank_bonus
                break
        for support_rank_bonus in aff2.bonus:
            if support_rank_bonus.support_rank == highest_rank:
                aff2_bonus = support_rank_bonus
                break

        # Get bonus to stats from specific pairing
        specific_bonus = self.get_specific_bonus(unit1, unit2, highest_rank)

        # Build final bonus
        final_bonus = SupportEffect()

        method = DB.support_constants.value('bonus_method')
        if method == 'Use Personal Affinity Bonus':
            if aff1_bonus:
                final_bonus.add_effect(aff1_bonus.effects)
        elif method == "Use Partner's Affinity Bonus":
            if aff2_bonus:
                final_bonus.add_effect(aff2_bonus.effects)
        elif method == 'Use Average of Affinity Bonuses':
            if aff1_bonus and aff2_bonus:
                final_bonus.add_effect([_/2. for _ in aff1_bonus.effects])
                final_bonus.add_effect([_/2. for _ in aff2_bonus.effects])
        elif method == 'Use Sum of Affinity Bonuses':
            if aff1_bonus and aff2_bonus:
                final_bonus.add_effect(aff1_bonus.effects)
                final_bonus.add_effect(aff2_bonus.effects)

        if specific_bonus:
            final_bonus.add_effect(specific_bonus.effects)

        return final_bonus
