from app.engine import item_system

def can_wield(unit, item) -> bool:
    weapon = item_system.is_weapon(unit, item)
    spell = item_system.is_weapon(unit, item)
    available = item_system.available(unit, item)
    if (weapon or spell):
        if available:
            return True
        else:
            return False
    return True
