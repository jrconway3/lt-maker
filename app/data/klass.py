try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data
from app import utilities

class Klass(object):
    def __init__(self, nid, short_name, long_name, desc, tier, movement_group, 
                 promotes_from, turns_into, tags, max_level,
                 bases, growths, promotion, max_stats,
                 skills, wexp_gain, growth_bonus=None, 
                 icon_fn=None, icon_index=(0, 0)):
        self.nid = nid
        self.short_name = short_name
        self.long_name = long_name

        self.desc = desc
        self.tier = tier
        self.movement_group = movement_group

        self.promotes_from = promotes_from
        self.turns_into = turns_into

        self.tags = tags

        self.bases = bases
        self.growths = growths
        self.growth_bonus = growth_bonus
        self.promotion = promotion
        self.max_stats = max_stats

        self.skills = skills
        self.wexp_gain = wexp_gain

        self.max_level = max_level
        self.exp_mult = 1
        self.opponent_exp_mult = 1

        self.icon_fn = icon_fn
        self.icon_index = icon_index

class ClassCatalog(data):
    def import_xml(self, xml_fn):
        class_data = ET.parse(xml_fn)
        for klass in class_data.getroot().findall('class'):
            nid = klass.get('id')
            short_name = klass.find('short_name').text
            long_name = klass.find('long_name').text
            tier = int(klass.find('tier').text)
            promotes_from = klass.find('promotes_from').text if klass.find('promotes_from').text is not None else None
            turns_into = klass.find('turns_into').text if klass.find('turns_into').text is not None else []
            movement_group = klass.find('movement_group').text
            max_level = klass.find('max_level').text
            tags = set(klass.find('tags').text.split(',')) if klass.find('tags').text is not None else set()
            desc = klass.find('desc').text

            bases = utilities.intify(klass.find('bases').text)
            growths = utilities.intify(klass.find('growths').text)
            promotion = utilities.intify(klass.find('promotion').text)
            max_stats = utilities.intify(klass.find('max').text)

            skills = utilities.skill_parser(klass.find('skills').text)
            wexp_gain = klass.find('wexp_gain').text.split(',')
            for index, wexp in enumerate(wexp_gain[:]):
                if wexp in db.weapon_ranks:
                    wexp_gain[index] = db.weapon_ranks[wexp].requirement

            new_klass = Klass(nid, short_name, long_name, desc, tier, movement_group, 
                              promotes_from, turns_into, tags, max_level,
                              bases, growths, promotion, max_stats,
                              skills, wexp_gain)
            self.append(new_klass)
