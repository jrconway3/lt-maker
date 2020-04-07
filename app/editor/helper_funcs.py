from app.data.database import DB

def can_wield(unit, item, prefab=False):
    if (item.weapon or item.spell) and item.level:
        weapon_rank = DB.weapon_ranks.get(item.level.value)
        req = weapon_rank.requirement
        comp = item.weapon if item.weapon else item.spell
        if prefab:
            wexp_gain_data = unit.wexp_gain.get(comp.value)
        else:
            klass = DB.classes.get(unit.klass)
            wexp_gain_data = klass.wexp_gain.get(comp.value)
        if wexp_gain_data and wexp_gain_data.usable:
            if not prefab and unit.generic:
                return True
            if wexp_gain_data.wexp_gain >= req:
                return True
        return False
    elif item.prf_unit:
        if unit.nid in item.prf_unit.value.keys():
            return True
        else:
            return False
    elif item.prf_class:
        if unit.klass in item.prf_class.value.keys():
            return True
        else:
            return False
    else:
        return True
