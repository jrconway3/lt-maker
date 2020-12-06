from app.data.database import DB

from app.engine import item_system, skill_system
from app.engine.objects.item import ItemObject
from app.engine.objects.skill import SkillObject

def is_magic(unit, item) -> bool:
    weapon_type = item_system.weapon_type(unit, item)
    if weapon_type and DB.weapons.get(weapon_type).magic:
        return True
    if item.magic:
        return True
    return False

def create_items(unit, item_nid_list: list) -> list:
    items = []
    for item_nid, droppable in item_nid_list:
        item_prefab = DB.items.get(item_nid)
        item = ItemObject.from_prefab(item_prefab)
        item.owner_nid = unit.nid
        item.droppable = droppable
        item_system.init(unit, item)
        items.append(item)
    return items

def get_all_items(unit) -> list:
    """
    Use this to get all weapons if you want to be able to handle multi_items
    """
    
    items = []
    for item in unit.items:
        if item.multi_item:
            for subitem in item.multi_item.value:
                items.append(subitem)
        else:
            items.append(item)
    return items

def get_all_tradeable_items(unit) -> list:
    items = []
    for item in unit.items:
        if not item_system.locked(unit, item):
            items.append(item)
    return items

def inventory_full(unit, item) -> bool:
    if item_system.is_accessory(unit, item):
        return len(unit.accessories) >= DB.constants.value('num_accessories')
    else:
        return len(unit.nonaccessories) >= DB.constants.value('num_items')

def get_range_string(unit, item):
    if unit:
        item_range = item_system.get_range(unit, item)
        min_range = min(item_range)
        max_range = max(item_range)
    else:
        min_range = item_system.minimum_range(None, item)
        max_range = item_system.maximum_range(None, item)
    if min_range != max_range:
        rng = '%d-%d' % (min_range, max_range)
    else:
        rng = '%d' % max_range
    return rng

# Skill stuff
def create_skills(unit, skill_nid_list: list) -> list:
    skills = []
    for skill_nid in skill_nid_list:
        skill_prefab = DB.skills.get(skill_nid)
        skill = SkillObject.from_prefab(skill_prefab)
        skill.owner_nid = unit.nid
        skill_system.init(unit, skill)
        skills.append(skill)
    return skills
