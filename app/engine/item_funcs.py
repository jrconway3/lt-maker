from app.data.database import DB

from app.engine import item_system

def is_magic(unit, item) -> bool:
    weapon_type = item_system.weapon_type(unit, item)
    if weapon_type and DB.weapons.get(weapon_type).magic:
        return True
    if item.magic:
        return True
    return False

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
