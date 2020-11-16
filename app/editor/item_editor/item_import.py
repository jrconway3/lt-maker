import xml.etree.ElementTree as ET

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB
from app.data import items

from app.data.components import Type

import app.engine.item_component_access as ICA

def get_from_xml(parent_dir: str, xml_fn: str) -> list:
    item_xml = ET.parse(xml_fn)
    item_list = []
    for item in item_xml.getroot().findall('item'):
        nids = DB.items.keys()
        nid = str_utils.get_next_name(item.find('id').text, nids)
        name = item.get('name')
        desc = item.find('desc').text
        icon_nid = item.find('spritetype').text
        icon_index = item.find('spriteid').text.split(',')
        if len(icon_index) == 1:
            icon_index = (0, int(icon_index[0]))
        else:
            icon_index = (int(icon_index[0]), int(icon_index[1]))

        components = item.find('components').text.split(',')
        final_components = Data()
        for component in components:
            if component == 'weapon':
                weapon_comp = ICA.get_component('weapon')
                final_components.append(weapon_comp)
                target_comp = ICA.get_component('target_enemy')
                final_components.append(target_comp)
                exp_comp = ICA.get_component('level_exp')
                final_components.append(exp_comp)
                damage_comp = ICA.get_component('damage')
                damage_comp.value = int(item.find('MT').text)
                final_components.append(damage_comp)
                hit_comp = ICA.get_component('hit')
                hit_comp.value = int(item.find('HIT').text)
                final_components.append(hit_comp)
                wtype = item.find('weapontype').text
                if wtype in DB.weapons.keys():
                    weapontype_comp = ICA.get_component('weapon_type')
                    weapontype_comp.value = wtype
                    final_components.append(weapontype_comp)
                wrank = item.find('LVL').text
                if wrank in DB.weapon_ranks.keys():
                    weaponrank_comp = ICA.get_component('weapon_rank')
                    weaponrank_comp.value = wrank
                    final_components.append(weaponrank_comp)

            elif item.find(component):
                comp = ICA.get_component(component)
                if comp:
                    value = item.find(component).text
                    if comp.expose == Type.Int:
                        value = int(value)
                    elif comp.expose == Type.Float:
                        value = float(value)
                    comp.value = value
                    final_components.append(comp)
            else:
                comp = ICA.get_component(component)
                if comp:
                    final_components.append(comp)

        # Handle item value
        value = int(item.find('value').text)
        if value > 0:
            comp = ICA.get_component('value')
            if item.find('uses'):
                value *= int(item.find('uses').text)
            comp.value = value
            final_components.append(comp)

        # Handle item range
        rng = item.find('RNG').text.split('-')
        if len(rng) == 1 and int(rng[0]) > 0:
            comp = ICA.get_component('min_range')
            comp.value = int(rng[0])
            final_components.append(comp)
            comp = ICA.get_component('max_range')
            comp.value = int(rng[0])
            final_components.append(comp)
        elif len(rng) == 2:
            comp = ICA.get_component('min_range')
            comp.value = int(rng[0])
            final_components.append(comp)
            if rng[1] == 'MAG/2':
                comp = ICA.get_component('equation_max_range')
                comp.value = 'MAG_RANGE'
            else:
                comp = ICA.get_component('max_range')
                comp.value = int(rng[1])
            final_components.append(comp)

        new_item = items.ItemPrefab(nid, name, desc, icon_nid, icon_index, final_components)

        item_list.append(new_item)
    return item_list
