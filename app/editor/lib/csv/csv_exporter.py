

from app.data.database import Database
from app.data.items import ItemCatalog
from app.data.klass import ClassCatalog
from app.data.units import UnitCatalog

def item_db_to_csv(item_db: ItemCatalog) -> str:
    """Generates a csv of all relevant weapons.

    Because items is a massive, massive umbrella, this function will define 'relevant'
    as being a siege weapon, weapon, or spell. Of these weapons, this will list the typical FE
    properties:
    - Hit
    - Crit
    - Might
    - Rank and Type
    - Weight
    - Uses
    - Value
    - Range

    Returns:
        str: csv-ified string.
    """
    if not item_db._list:
        return ""
    def get_or_null(i, at):
        if i[at]:
            return i[at].value
        else:
            return '--'
    # header
    headers = ['NAME', 'NID', 'HIT', 'CRIT', 'MIGHT', 'TYPE', 'RANK', 'WEIGHT', 'USES', 'MIN_RANGE', 'MAX_RANGE', 'VALUE']
    ss = ','.join(headers) + "\n"
    for item in item_db:
        if item.hit or item.might or item.weapon_type:
            data = [item.name, item.nid]
            for attribute in ['hit', 'crit', 'damage', 'weapon_type', 'weapon_rank', 'weight', 'uses', 'min_range', 'max_range', 'value']:
                data.append(get_or_null(item, attribute))
            ss += ','.join([str(dat) for dat in data]) + "\n"
    return ss

def unit_db_to_csv(unit_db: UnitCatalog):
    if not unit_db._list:
        return ""
    first_elem = unit_db._list[0]
    bases_d, _ = first_elem.get_stat_lists()
    weapons_l = list(first_elem.wexp_gain.keys())
    stats_l = list(bases_d.keys())
    # header
    ss = "NAME,NID," + ''.join([stat + '_base,' for stat in stats_l]) + ''.join([stat + '_growth,' for stat in stats_l]) + ','.join(weapons_l) + "\n"
    for unit in unit_db:
        ss += unit.name + ',' + unit.nid + ','
        ubases, ugrowths = unit.get_stat_lists()
        wranks = unit.wexp_gain
        ss += ''.join([str(ubases[stat]) + ',' for stat in stats_l]) + ''.join([str(ugrowths[stat]) + ',' for stat in stats_l]) + ''.join([str(wranks[weapon].wexp_gain) + "," for weapon in weapons_l]) + "\n"
    return ss

def klass_db_to_csv(klass_db: ClassCatalog):
    if not klass_db._list:
        return ""
    first_elem = klass_db._list[0]
    bases_d, growths_d, gains_d, growth_bonuses_d, stat_caps = first_elem.get_stat_lists()
    weapons_l = list(first_elem.wexp_gain.keys())
    stats_l = list(bases_d.keys())
    # header
    ss = "NAME,NID," + ''.join([stat + '_base,' for stat in stats_l]) + ''.join([stat + '_growth,' for stat in stats_l]) + ','.join(weapons_l) + "\n"
    for unit in klass_db:
        ss += unit.name + ',' + unit.nid + ','
        ubases, ugrowths, ugains, ubonuses, ucaps = unit.get_stat_lists()
        wranks = unit.wexp_gain
        ss += ''.join([str(ubases.get(stat, 0)) + ',' for stat in stats_l]) + ''.join([str(ugrowths.get(stat, 0)) + ',' for stat in stats_l]) + ''.join([str(bool(wranks[weapon].usable)) + "," for weapon in weapons_l]) + "\n"
    return ss

def dump_as_csv(db: Database):
    # csv dump functions
    return [
            ('units', unit_db_to_csv(db.units)),
            ('classes', klass_db_to_csv(db.classes)),
            ('items', item_db_to_csv(db.items)),
            ]