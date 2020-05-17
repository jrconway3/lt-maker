import xml.etree.ElementTree as ET

from dataclasses import dataclass

from app.data.data import Data, Prefab
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
    wexp_gain: weapons.WexpGainData = None

    portrait_nid: str = None

    def get_stat_titles(self):
        return ["Bases", "Growths"]

    def get_stat_lists(self):
        return [self.bases, self.growths]

    def get_items(self):
        return [i[0] for i in self.starting_items]

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def deserialize_attr(self, name, value):
        if name in ('bases', 'growths'):
            value = stats.StatList.deserialize(value)
        elif name == 'learned_skills':
            value = [LearnedSkill.deserialize(skill) for skill in value]
        elif name == 'wexp_gain':
            value = weapons.WexpGainData.deserialize(value)
        elif name == 'starting_items':
            # Need to convert to item nid + droppable
            value = [i if isinstance(i, list) else [i, False] for i in value]
        else:
            value = super().deserialize_attr(name, value)
        return value

@dataclass 
class GenericUnit(Prefab):
    nid: str = None
    gender: int = None

    level: int = None
    klass: str = None

    faction: str = None

    starting_items: list = None

    team: str = None
    ai: str = None

    starting_position: tuple = None

    name: str = None
    desc: str = None
    generic: bool = True

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def deserialize_attr(self, name, value):
        if name == 'starting_position':
            if value is not None:
                value = tuple(value)
        elif name == 'starting_items':
            # Need to convert to item nid + droppable
            value = [i if isinstance(i, list) else [i, False] for i in value]
        else:
            value = super().deserialize_attr(name, value)
        return value

    def restore_prefab(self, units):
        pass

@dataclass
class UniqueUnit(Prefab):
    nid: str = None
    prefab: UnitPrefab = None
    team: str = None
    ai: str = None

    starting_position: tuple = None

    generic: bool = False

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        elif self.prefab:
            return getattr(self.prefab, attr)
        return None 

    def serialize_attr(self, name, value):
        if name == 'prefab':
            value = self.nid
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name == 'starting_position':
            value = tuple(value)
        else:
            value = super().deserialize_attr(name, value)
        return value

    def restore_prefab(self, units):
        self.prefab = units.get(self.nid)

class UnitCatalog(Data):
    datatype = UnitPrefab
    
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

            bases = stats.StatList.from_xml(utilities.intify(unit.find('bases').text), stat_types)
            growths = stats.StatList.from_xml(utilities.intify(unit.find('growths').text), stat_types)

            skills = utilities.skill_parser(unit.find('skills').text)
            learned_skills = LearnedSkillList()
            for skill in skills:
                learned_skills.append(LearnedSkill(skill[0], skill[1]))

            wexp_gain = unit.find('wexp').text.split(',')
            for index, wexp in enumerate(wexp_gain[:]):
                if wexp in weapon_ranks.keys():
                    wexp_gain[index] = weapon_ranks.get(wexp).requirement
            wexp_gain = [int(i) for i in wexp_gain]
            wexp_gain = weapons.WexpGainData.from_xml(wexp_gain, weapon_types)

            starting_items = unit.find('inventory').text.split(',')  # List of nids
            # items = [i for i in items if i]

            new_unit = UnitPrefab(nid, name, desc, gender, level, klass, tags,
                                  bases, growths, starting_items, learned_skills, wexp_gain, nid)
            self.append(new_unit)
