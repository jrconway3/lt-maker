from app.data.data import Data
from app.data.item_component import ItemComponent, tags

# Necessary for get_item_components to find all the 
# item components defined in item_components folder
from app.engine import item_components

def get_item_components():
    subclasses = ItemComponent.__subclasses__() 
    # Sort by tag
    subclasses = sorted(subclasses, key=lambda x: tags.index(x.tag) if x.tag in tags else 100)
    return Data(subclasses)

def get_component(nid):
    _item_components = get_item_components()
    base = _item_components.get(nid)
    return ItemComponent.copy(base)

def deserialize_component(dat):
    nid, value = dat
    _item_components = get_item_components()
    base = _item_components.get(nid)
    copy = ItemComponent.copy(base)
    copy.value = value
    return copy
