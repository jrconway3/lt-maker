from app.data.item_components import ItemComponent
from app.data.components import Type

class MultiItem(ItemComponent):
    nid = 'multi_item'
    desc = "Item that contains multiple items. Don't abuse!"
    tag = 'advanced'

    expose = (Type.List, Type.Item)

class SequenceItem(ItemComponent):
    nid = 'sequence_item'
    desc = "Item that contains a sequence of items used for targeting"
    tag = 'advanced'

    expose = (Type.List, Type.Item)
