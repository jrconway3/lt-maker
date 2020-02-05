try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import data, Prefab
from app.data import stats, weapons
from app.data.skills import LearnedSkill, LearnedSkillList
from app import utilities

@dataclass
class UnitPrefab(Prefab):
    nid: str = None
    name: str = None
    desc: str = None
    gender: int = None

    level: int = None
    klass: str = None

    tags: list = None
    bases: stats.StatList = None
    growths: stats.StatList = None
    starting_items: list = None
    
    learned_skills: LearnedSkillList = None
    wexp_gain: weapons.WexpGainList = None

    portrait_nid: str = None

    def get_stat_lists(self):
        return [self.bases, self.growths]

class UnitCatalog(data):
    def import_xml(self, xml_fn, stat_types, weapon_types, weapon_ranks, item_catalog):
        unit_data = ET.parse(xml_fn)
        for unit in unit_data.getroot().findall('unit'):
            nid = unit.find('id').text
            name = unit.get('name')
            desc = unit.find('desc').text
            gender = int(unit.find('gender').text)
            level = int(unit.find('level').text)
            klass = unit.find('class').text
            if unit.find('tags').text is not None:
                tags = unit.find('tags').text.split(',')
            else:
                tags = []

            bases = stats.StatList(utilities.intify(unit.find('bases').text), stat_types)
            growths = stats.StatList(utilities.intify(unit.find('growths').text), stat_types)

            skills = utilities.skill_parser(unit.find('skills').text)
            learned_skills = LearnedSkillList()
            for skill in skills:
                learned_skills.append(LearnedSkill(skill[0], skill[1]))

            wexp_gain = unit.find('wexp').text.split(',')
            for index, wexp in enumerate(wexp_gain[:]):
                if wexp in weapon_ranks.keys():
                    wexp_gain[index] = weapon_ranks.get(wexp).requirement
            wexp_gain = [int(i) for i in wexp_gain]
            wexp_gain = weapons.WexpGainList(wexp_gain, weapon_types)

            starting_items = unit.find('inventory').text.split(',')  # List of nids
            # items = [i for i in items if i]

            new_unit = UnitPrefab(nid, name, desc, gender, level, klass, tags,
                                  bases, growths, starting_items, learned_skills, wexp_gain, nid)
            self.append(new_unit)
