from app.data.database import DB

from app.engine import item_system
from app.engine.objects.item import ItemObject

def is_magic(unit, item) -> bool:
    weapon_type = item_system.weapon_type(unit, item)
    if weapon_type and DB.weapons.get(weapon_type).magic:
        return True
    if item.magic:
        return True
    return False

def create_items(unit_nid, item_nid_list):
    items = []
    for item_nid, droppable in item_nid_list:
        item_prefab = DB.items.get(item_nid)
        item = ItemObject.from_prefab(item_prefab)
        item.owner_nid = unit_nid
        item.droppable = droppable
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
