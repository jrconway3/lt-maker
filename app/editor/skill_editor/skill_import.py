import xml.etree.ElementTree as ET

from app.utilities import str_utils, utils
from app.utilities.data import Data
from app.data.database import DB
from app.data import skills

from app.data.components import Type

import app.engine.skill_component_access as SCA

def get_from_xml(parent_dir: str, xml_fn: str) -> list:
    skill_xml = ET.parse(xml_fn)
    skill_list = []
    for skill in skill_xml.getroot().findall('status'):
        try:
            new_skill = load_skill(skill)
            skill_list.append(new_skill)
        except Exception as e:
            print("Skill %s Import Error: %s" % (skill.find('id').text, e))
    return skill_list

def load_skill(skill):
    nids = DB.skills.keys()
    nid = str_utils.get_next_name(skill.find('id').text, nids)
    name = skill.get('name')
    desc = skill.find('desc').text
    icon_nid = 'Skills'
    icon_index = skill.find('image_index').text.split(',')
    icon_index = (int(icon_index[0]), int(icon_index[1]))

    components = skill.find('components').text.split(',') if skill.find('components').text else []
    final_components = Data()
    for component in components:
        if skill.find(component) is not None:
            comp = SCA.get_component(component)
            if comp:
                try:
                    value = skill.find(component).text
                    if comp.expose == Type.Int:
                        value = int(value)
                    elif comp.expose == Type.Float:
                        value = float(value)
                    elif comp.expose == Type.Color3 or comp.expose == Type.Color4:
                        value = [utils.clamp(int(c), 0, 255) for c in value.split(',')]
                    elif isinstance(comp.expose, tuple):
                        print("%s: Could not determine value for component %s" % (nid, component))
                        value = []
                    comp.value = value
                except Exception as e:
                    print("%s: Could not determine value for component %s" % (nid, component))
                final_components.append(comp)
            else:
                print("%s: Could not determine corresponding LT maker component for %s" % (nid, component))
        else:
            comp = SCA.get_component(component)
            if comp:
                final_components.append(comp)
            else:
                print("%s: Could not determine corresponding LT maker component for %s" % (nid, component))

    new_skill = skills.SkillPrefab(nid, name, desc, icon_nid, icon_index, final_components)
    return new_skill
