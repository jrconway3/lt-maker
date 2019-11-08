try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from app.data.data import data
from app.data import stats, weapons
from app.data.skills import LearnedSkill, LearnedSkillList
from app import utilities

class Klass(object):
    def __init__(self, nid: str, short_name: str, long_name: str,
                 desc: str, tier: int, movement_group: str, 
                 promotes_from, turns_into, tags, max_level: int,
                 bases: stats.StatList, growths: stats.StatList, promotion: stats.StatList, max_stats: stats.StatList,
                 skills: LearnedSkillList, wexp_gain: weapons.WexpGainList, growth_bonus: stats.StatList, 
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

        # Stat stuff
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

    def get_stat_lists(self):
        return [self.bases, self.growths, self.promotion, self.growth_bonus, self.max_stats]

class ClassCatalog(data):
    def import_xml(self, xml_fn, stat_types, weapon_types, weapon_ranks):
        class_data = ET.parse(xml_fn)
        for klass in class_data.getroot().findall('class'):
            nid = klass.get('id')
            short_name = klass.find('short_name').text
            long_name = klass.find('long_name').text
            tier = int(klass.find('tier').text)
            promotes_from = klass.find('promotes_from').text if klass.find('promotes_from').text is not None else None
            turns_into = klass.find('turns_into').text if klass.find('turns_into').text is not None else []
            movement_group = klass.find('movement_group').text
            max_level = int(klass.find('max_level').text)
            tags = klass.find('tags').text.split(',') if klass.find('tags').text is not None else []
            desc = klass.find('desc').text

            bases = stats.StatList(utilities.intify(klass.find('bases').text), stat_types)
            growths = stats.StatList(utilities.intify(klass.find('growths').text), stat_types)
            promotion = stats.StatList(utilities.intify(klass.find('promotion').text) if klass.find('promotion') else [0] * len(bases), stat_types)
            max_stats = stats.StatList(utilities.intify(klass.find('max').text), stat_types)
            growth_bonus = stats.StatList(utilities.intify(klass.find('growth_bonus').text) if klass.find('growth_bonus') else [0] * len(growths), stat_types)

            skills = utilities.skill_parser(klass.find('skills').text)
            learned_skills = LearnedSkillList()
            for skill in skills:
                learned_skills.append(LearnedSkill(skill[0], skill[1]))

            wexp_gain = klass.find('wexp_gain').text.split(',')
            for index, wexp in enumerate(wexp_gain[:]):
                if wexp in weapon_ranks:
                    wexp_gain[index] = weapon_ranks[wexp].requirement
            wexp_gain = weapons.WexpGainList(wexp_gain, weapon_types)

            new_klass = Klass(nid, short_name, long_name, desc, tier, movement_group, 
                              promotes_from, turns_into, tags, max_level,
                              bases, growths, promotion, max_stats,
                              skills, wexp_gain, growth_bonus)
            self.append(new_klass)
