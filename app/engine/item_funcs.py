from app.data.database import DB

def is_magic(item):
    weapon_type = None
    if item.weapon:
        weapon_type = item.weapon.value
    elif item.spell:
        weapon_type = item.spell.weapon_type
    if weapon_type and DB.weapons.get(weapon_type).magic:
        return True
    if item.magic:
        return True
