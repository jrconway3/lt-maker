from app.engine.item_system.item_component import ItemComponent, Type

class MultiItem(ItemComponent):
    nid = 'multi_item'
    desc = "Item that contains multiple items. Don't abuse!"
    expose = (Type.Set, Type.Item)
