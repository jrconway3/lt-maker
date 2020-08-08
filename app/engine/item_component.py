from app.data.item_components import ItemComponent

# Necessary for get_item_components to find all the 
# item components defined in item_components folder
from app.engine import item_components

def get_item_components():
    return {i.nid: i for i in ItemComponent.__subclasses__()}

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
