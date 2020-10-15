from app.utilities.data import Data
from app.data.item_components import ItemComponent, tags

def get_item_components():
    # Necessary for get_item_components to find all the 
    # item components defined in item_components folder
    from app.engine import item_components

    subclasses = ItemComponent.__subclasses__() 
    # Sort by tag
    subclasses = sorted(subclasses, key=lambda x: tags.index(x.tag) if x.tag in tags else 100)
    return Data(subclasses)

def get_component(nid):
    _item_components = get_item_components()
    base_class = _item_components.get(nid)
    return base_class(base_class.value)

def restore_component(dat):
    nid, value = dat
    _item_components = get_item_components()
    base_class = _item_components.get(nid)
    copy = base_class(value)
    return copy

templates = {'Weapon': ('weapon', 'value', 'target_enemy', 'min_range', 'max_range', 'damage', 'hit', 'crit', 'weight', 'level_exp', 'weapon_type', 'weapon_rank'),
             'Spell': ('spell', 'value', 'min_range', 'max_range', 'weapon_type', 'weapon_rank'),
             'Usable': ('value', 'target_ally', 'uses')}

def get_templates():
    return templates.items()
