try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from collections import OrderedDict

from app.data.data import data
from app import utilities

class WeaponRank(object):
    def __init__(self, rank, requirement, accuracy=0, damage=0, crit=0):
        self.rank = rank
        self.requirement = requirement
        self.accuracy = accuracy
        self.damage = damage
        self.crit = crit

    @property
    def nid(self):
        return self.rank

    def __repr__(self):
        return "Weapon Rank %s: %d -- (%d, %d, %d)" % \
            (self.rank, self.requirement, self.accuracy, self.damage, self.crit)

class RankCatalog(data):
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

class WeaponType(object):
    def __init__(self, nid, name, magic, advantage, disadvantage, icon_fn=None, icon_index=(0, 0)):
        self.nid = nid
        self.name = name
        self.magic = magic
        self.advantage = advantage
        self.disadvantage = disadvantage

        self.icon_fn = icon_fn
        self.icon_index = icon_index

class WexpGain(object):
    def __init__(self, usable: bool, weapon_type: WeaponType, wexp_gain: int):
        self.usable = usable
        self.weapon_type = weapon_type
        self.wexp_gain = wexp_gain

class WexpGainList(OrderedDict):
    def __init__(self, data, weapon_types):
        for i in range(len(weapon_types)):
            key = weapon_types[i].nid
            self[key] = WexpGain(bool(data[i]), key, data[i])

    def remove_key(self, key):
        del self[key]

    def change_key(self, old_key, new_key):
        old_value = self[old_key]
        del self[old_key]
        self[new_key] = old_value

    def new_key(self, key):
        self[key] = WexpGain(False, key, 0)

class Advantage(object):
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

class AdvantageList(list):
    def add_new_default(self, db):
        if len(self):
            new_advantage = Advantage(self[-1].weapon_type, self[-1].weapon_rank, (0, 0, 0, 0, 0, 0, 0))
        else:
            new_advantage = Advantage(db.weapons[0].nid, db.weapon_ranks[0].rank, (0, 0, 0, 0, 0, 0, 0))
        self.append(new_advantage)

class WeaponCatalog(data):
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
                           'sprites/wexp_icons.png', (0, idx))
            self.append(new_weapon_type)
