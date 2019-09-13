try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

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

class RankData(data):
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

    def add_new_default(self):
        new_name = utilities.get_next_name('RANK', [d.rank for d in self.values()])
        new_rank = WeaponRank(new_name, 1)
        self.append(new_rank)

class WeaponType(object):
    def __init__(self, nid, name, magic, advantage, disadvantage, sprite_fn=None, sprite_index=None):
        self.nid = nid
        self.name = name
        self.magic = magic
        self.advantage = advantage
        self.disadvantage = disadvantage

        self.sprite_fn = sprite_fn
        self.sprite_index = sprite_index

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
        self.AS = effects[6]

class WeaponData(data):
    def import_xml(self, xml_fn):
        weapon_data = ET.parse(xml_fn)
        for weapon in weapon_data.getroot().findall('stat'):
            name = weapon.get('name')
            nid = weapon.find('id').text
            magic = bool(int(weapon.find('magic').text))
            advantage = []
            for adv in weapon.findall('advantage'):
                weapon_type = adv.get('type')
                rank = adv.find('rank').text
                effects = adv.find('effects').text.split(',')
                advantage.append(Advantage(weapon_type, rank, effects))
            disadvantage = []
            for adv in weapon.findall('disadvantage'):
                weapon_type = adv.get('type')
                rank = adv.find('rank').text
                effects = adv.find('effects').text.split(',')
                disadvantage.append(Advantage(weapon_type, rank, effects))
            new_weapon_type = WeaponType(nid, name, magic, advantage, disadvantage)
            self.append(new_weapon_type)
