try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import Data, Prefab
from app import utilities

# === WEAPON RANK ===
@dataclass
class WeaponRank(Prefab):
    rank: str = None
    requirement: int = 1
    accuracy: int = 0
    damage: int = 0
    crit: int = 0

    @property
    def nid(self):
        return self.rank

    def __repr__(self):
        return "WeaponRank %s: %d -- (%d, %d, %d)" % \
            (self.rank, self.requirement, self.accuracy, self.damage, self.crit)

class RankCatalog(Data):
    datatype = WeaponRank

    def import_data(self, txt_fn):
        with open(txt_fn) as fp:
            lines = [line.strip() for line in fp.readlines() if not line.strip().startswith('#')]
            for line in lines:
                s_l = line.split(';')
                rank = s_l[0]
                requirement = int(s_l[1])
                if len(s_l) > 2:
                    accuracy, damage, crit = int(s_l[2]), int(s_l[3]), int(s_l[4])
                else:
                    accuracy, damage, crit = 0, 0, 0
                new_rank = WeaponRank(rank, requirement, accuracy, damage, crit)
                self.append(new_rank)

    def add_new_default(self, db):
        new_name = utilities.get_next_name('RANK', [d.rank for d in self.values()])
        new_rank = WeaponRank(new_name, 1)
        self.append(new_rank)

# === WEAPON ADVANTAGE AND DISADVANTAGE ===
class Advantage(Prefab):
    def __init__(self, weapon_type, weapon_rank, effects):
        self.weapon_type = weapon_type
        self.weapon_rank = weapon_rank

        self.damage = effects[0]
        self.resist = effects[1]
        self.accuracy = effects[2]
        self.avoid = effects[3]
        self.crit = effects[4]
        self.dodge = effects[5]
        self.attackspeed = effects[6]

    @property
    def effects(self):
        return (self.damage, self.resist, self.accuracy, self.avoid, self.crit, self.dodge, self.attackspeed)

    @classmethod
    def default(cls):
        return cls(None, None, [0]*7)

class AdvantageList(list):
    def add_new_default(self, db):
        if len(self):
            new_advantage = Advantage(self[-1].weapon_type, self[-1].weapon_rank, (0, 0, 0, 0, 0, 0, 0))
        else:
            new_advantage = Advantage(db.weapons[0], db.weapon_ranks[0].rank, (0, 0, 0, 0, 0, 0, 0))
        self.append(new_advantage)

    def contains(self, weapon_type):
        return any(advantage.weapon_type == weapon_type for advantage in self)

    def swap(self, old_weapon_type, new_weapon_type):
        for advantage in self:
            if advantage.weapon_type == old_weapon_type:
                advantage.weapon_type = new_weapon_type

# === WEAPON TYPE ===
@dataclass(eq=False)
class WeaponType(Prefab):
    nid: str = None
    name: str = None
    magic: bool = False
    advantage: AdvantageList = None
    disadvantage: AdvantageList = None

    icon_nid: str = None
    icon_index: tuple = (0, 0)

    def __repr__(self):
        return ("WeaponType %s" % self.nid)

    def serialize_attr(self, name, value):
        if name in ('advantage', 'disadvantage'):
            value = [adv.serialize() for adv in value]
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name in ('advantage', 'disadvantage'):
            value = AdvantageList([Advantage.deserialize(adv) for adv in value])
        else:
            value = super().deserialize_attr(name, value)
        return value

class WeaponCatalog(Data):
    datatype = WeaponType

    def import_xml(self, xml_fn):
        weapon_data = ET.parse(xml_fn)
        for idx, weapon in enumerate(weapon_data.getroot().findall('weapon')):
            name = weapon.get('name')
            nid = weapon.find('id').text
            magic = bool(int(weapon.find('magic').text))
            advantage = AdvantageList()
            for adv in weapon.findall('advantage'):
                weapon_type = adv.get('type')
                rank = adv.find('rank').text
                effects = adv.find('effects').text.split(',')
                advantage.append(Advantage(weapon_type, rank, effects))
            disadvantage = AdvantageList()
            for adv in weapon.findall('disadvantage'):
                weapon_type = adv.get('type')
                rank = adv.find('rank').text
                effects = adv.find('effects').text.split(',')
                disadvantage.append(Advantage(weapon_type, rank, effects))
            new_weapon_type = \
                WeaponType(nid, name, magic, advantage, disadvantage, 
                           'wexp_icons', (0, idx))
            self.append(new_weapon_type)


# === WEAPON EXPERIENCE GAINED ===
class WexpGain(Prefab):
    def __init__(self, usable: bool, weapon_type: str, wexp_gain: int):
        self.usable = usable
        self.nid = weapon_type
        self.wexp_gain = wexp_gain

    def absorb(self, wexp_gain):
        self.usable = wexp_gain.usable
        self.wexp_gain = wexp_gain.wexp_gain

    def serialize(self):
        return (self.usable, self.nid, self.wexp_gain)

    @property
    def weapon_type(self):
        return self.nid
    
    @classmethod
    def deserialize(cls, s_tuple):
        return cls(*s_tuple)

class WexpGainData(Data):
    datatype = WexpGain

    @classmethod
    def from_xml(cls, data, weapon_types):
        new_wexpgain = cls()
        for i in range(len(weapon_types)):
            if i < len(data):
                d = int(data[i])
                new_wexpgain.append(WexpGain(bool(d), weapon_types[i].nid, d))
            else:
                new_wexpgain.append(WexpGain(False, weapon_types[i].nid, 0))
        return new_wexpgain

    def new(self, idx, weapon_types):
        self.insert(idx, WexpGain(False, weapon_types[idx].nid, 0))

    @classmethod
    def deserialize(cls, values):
        new_wexpgain = cls()
        for val in values:
            new_wexpgain.append(WexpGain.deserialize(val))
        return new_wexpgain
