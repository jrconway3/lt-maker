try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import Data, Prefab
from app.data import stats, weapons
from app.data.skills import LearnedSkill, LearnedSkillList
from app import utilities

@dataclass
class Klass(Prefab):
    nid: str = None
    short_name: str = None
    long_name: str = None

    desc: str = ""
    tier: int = 1
    movement_group: str = None

    promotes_from: str = None
    turns_into: list = None
    tags: list = None
    max_level: int = 20

    bases: stats.StatList = None
    growths: stats.StatList = None
    growth_bonus: stats.StatList = None
    promotion: stats.StatList = None
    max_stats: stats.StatList = None

    learned_skills: LearnedSkillList = None
    wexp_gain: weapons.WexpGainData = None

    icon_nid: str = None
    icon_index: tuple = (0, 0)
    map_sprite_nid: str = None

    exp_mult: float = 1.
    opponent_exp_mult: float = 1.

    def get_stat_titles(self):
        return ['Generic Bases', 'Generic Growths', 'Promotion Gains', 'Growth Bonuses', 'Stat Maximums']

    def get_stat_lists(self):
        return [self.bases, self.growths, self.promotion, self.growth_bonus, self.max_stats]

    def serialize_attr(self, name, value):
        if name == 'learned_skills':
            value = [skill.serialize() for skill in value]
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name in ('bases', 'growths', 'growth_bonus', 'promotion', 'max_stats'):
            value = stats.StatList.deserialize(value)
        elif name == 'learned_skills':
            value = [LearnedSkill.deserialize(skill) for skill in value]
        elif name == 'wexp_gain':
            value = weapons.WexpGainData.deserialize(value)
        else:
            value = super().deserialize_attr(name, value)
        return value

class ClassCatalog(Data):
    datatype = Klass

    def import_xml(self, xml_fn, stat_types, weapon_types, weapon_ranks):
        class_data = ET.parse(xml_fn)
        for klass in class_data.getroot().findall('class'):
            nid = klass.get('id')
            short_name = klass.find('short_name').text
            long_name = klass.find('long_name').text
            tier = int(klass.find('tier').text)
            promotes_from = klass.find('promotes_from').text if klass.find('promotes_from').text is not None else None
            turns_into = klass.find('turns_into').text.split(',') if klass.find('turns_into').text is not None else []
            movement_group = klass.find('movement_group').text
            max_level = int(klass.find('max_level').text)
            tags = klass.find('tags').text.split(',') if klass.find('tags').text is not None else []
            desc = klass.find('desc').text

            bases = stats.StatList.from_xml(utilities.intify(klass.find('bases').text), stat_types)
            growths = stats.StatList.from_xml(utilities.intify(klass.find('growths').text), stat_types)
            promotion = stats.StatList.from_xml(utilities.intify(klass.find('promotion').text) if klass.find('promotion') else [0] * len(bases), stat_types)
            max_stats = stats.StatList.from_xml(utilities.intify(klass.find('max').text), stat_types)
            growth_bonus = stats.StatList.from_xml(utilities.intify(klass.find('growth_bonus').text) if klass.find('growth_bonus') else [0] * len(growths), stat_types)

            skills = utilities.skill_parser(klass.find('skills').text)
            learned_skills = LearnedSkillList()
            for skill in skills:
                learned_skills.append(LearnedSkill(skill[0], skill[1]))

            wexp_gain = klass.find('wexp_gain').text.split(',')
            for index, wexp in enumerate(wexp_gain[:]):
                if wexp in weapon_ranks.keys():
                    wexp_gain[index] = weapon_ranks.get(wexp).requirement
            wexp_gain = [int(i) for i in wexp_gain]
            wexp_gain = weapons.WexpGainData.from_xml(wexp_gain, weapon_types)

            new_klass = Klass(nid, short_name, long_name, desc, tier, movement_group, 
                              promotes_from, turns_into, tags, max_level,
                              bases, growths, growth_bonus, promotion, max_stats,
                              learned_skills, wexp_gain)
            self.append(new_klass)
