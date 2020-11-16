import xml.etree.ElementTree as ET

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB
from app.data import skills

from app.data.components import Type

import app.engine.skill_component_access as SCA

def get_from_xml(parent_dir: str, xml_fn: str) -> list:
    skill_xml = ET.parse(xml_fn)
    skill_list = []
    for skill in skill_xml.getroot().findall('status'):
        nids = DB.skills.keys()
        nid = str_utils.get_next_name(skill.find('id').text, nids)
        name = skill.get('name')
        desc = skill.find('desc').text
        icon_nid = 'Skills'
        icon_index = skill.find('image_index').text.split(',')
        icon_index = (int(icon_index[0]), int(icon_index[1]))

        components = skill.find('components').text.split(',')
        final_components = Data()
        for component in components:
            if skill.find(component):
                comp = SCA.get_component(component)
                if comp:
                    value = skill.find(component).text
                    if comp.expose == Type.Int:
                        value = int(value)
                    elif comp.expose == Type.Float:
                        value = float(value)
                    comp.value = value
                    final_components.append(comp)
            else:
                comp = SCA.get_component(component)
                if comp:
                    final_components.append(comp)

        new_skill = skills.SkillPrefab(nid, name, desc, icon_nid, icon_index, final_components)

        skill_list.append(new_skill)
    return skill_list
