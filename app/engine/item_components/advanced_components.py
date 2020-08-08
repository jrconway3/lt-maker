from app.data.item_component import ItemComponent, Type

class MultiItem(ItemComponent):
    nid = 'multi_item'
    desc = "Item that contains multiple items. Don't abuse!"
    expose = (Type.List, Type.Item)

class SequenceItem(ItemComponent):
    nid = 'sequence_item'
    desc = "Item that contains a sequence of items used for targeting"
    expose = (Type.List, Type.Item)
