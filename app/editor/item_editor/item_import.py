import xml.etree.ElementTree as ET

from app.utilities import str_utils, utils
from app.utilities.data import Data
from app.data.database import DB
from app.data import items

from app.data.components import Type

import app.engine.item_component_access as ICA

def get_from_xml(parent_dir: str, xml_fn: str) -> list:
    item_xml = ET.parse(xml_fn)
    item_list = []
    for item in item_xml.getroot().findall('item'):
        try:
            new_item = load_item(item)
            item_list.append(new_item)
        except Exception as e:
            print("Item %s Import Error: %s" % (item.find('id').text, e))
    return item_list

def load_item(item):
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

    components = item.find('components').text.split(',') if item.find('components').text else []
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

        elif component == 'usable':
            usable = ICA.get_component('usable')
            final_components.append(usable)
            target_comp = ICA.get_component('target_ally')
            final_components.append(target_comp)

        elif component == 'status':
            comp = ICA.get_component('status_on_hit')
            comp.value = item.find('status').text
            final_components.append(comp)

        elif component == 'reverse':
            comp = ICA.get_component('reaver')
            final_components.append(comp)

        elif component == 'permanent_stat_increase':
            comp = ICA.get_component('permanent_stat_change')
            print("%s: Could not determine value for component %s" % (nid, 'permanent_stat_change'))
            comp.value = []
            final_components.append(comp)

        elif component == 'booster':
            comp = ICA.get_component('usable_in_base')
            final_components.append(comp)

        elif component == 'sfx_on_hit':
            comp = ICA.get_component('map_hit_sfx')
            comp.value = item.find('sfx_on_hit').text
            final_components.append(comp)

        elif component == 'sfx_on_cast':
            comp = ICA.get_component('map_cast_sfx')
            comp.value = item.find('sfx_on_cast').text
            final_components.append(comp)

        elif component in ('beneficial', 'detrimental'):
            # This is not necessary with BEEG update
            # All of beneficials varied functions
            # Mostly AI and targeting now need to be done
            # in their respective places
            pass

        elif item.find(component) is not None:
            comp = ICA.get_component(component)
            if comp:
                try:
                    value = item.find(component).text
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
            comp = ICA.get_component(component)
            if comp:
                final_components.append(comp)
            else:
                print("%s: Could not determine corresponding LT maker component for %s" % (nid, component))

    # Handle item value
    value = int(item.find('value').text)
    if value > 0:
        comp = ICA.get_component('value')
        if item.find('uses') is not None:
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
    return new_item
