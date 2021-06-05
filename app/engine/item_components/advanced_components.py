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

class MultiTarget(ItemComponent):
    nid = 'multi_target'
    desc = "Item can target multiple targets."
    tag = 'advanced'

    expose = Type.Int
    value = 2

    def num_targets(self, unit, item) -> int:
        return self.value

class AllowSameTarget(ItemComponent):
    nid = 'allow_same_target'
    desc = "Item can target the same target multiple times"
    tag = 'advanced'

    def allow_same_target(self, unit, item) -> bool:
        return True
