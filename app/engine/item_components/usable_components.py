from app.data.item_component import ItemComponent, Type

from app.engine import action

class Uses(ItemComponent):
    nid = 'uses'
    desc = "Number of uses of item"
    expose = Type.Int
    tag = 'uses'

    def init(self, item):
        item.data['uses'] = self.value

    def available(self, unit, item) -> bool:
        return item.data['uses'] > 0

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'uses', -1))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'uses', -1))

    def on_not_usable(self, unit, item):
        action.do(action.RemoveItem(unit, item))
        return True

class ChapterUses(ItemComponent):
    nid = 'c_uses'
    desc = "Number of uses per chapter for item. (Refreshes after each chapter)"
    expose = Type.Int
    tag = 'uses'

    def init(self, item):
        item.data['uses'] = self.value

    def available(self, unit, item) -> bool:
        return item.data['c_uses'] > 0

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'c_uses', -1))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.IncItemData(item, 'c_uses', -1))

    def on_end_chapter(self, unit, item):
        # Don't need to use action here because it will be end of chapter
        item.data['c_uses'] = self.starting_uses

class HPCost(ItemComponent):
    nid = 'hp_cost'
    desc = "Item costs HP to use"
    expose = Type.Int
    tag = 'uses'

    def available(self, unit, item) -> bool:
        return unit.get_hp() > self.hp_cost

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeHP(unit, -self.value))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeHP(unit, -self.value))

class ManaCost(ItemComponent):
    nid = 'mana_cost'
    desc = "Item costs mana to use"
    expose = Type.Int
    tag = 'uses'

    def available(self, unit, item) -> bool:
        return unit.get_mana() > self.mana_cost

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeMana(unit, -self.value))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.ChangeMana(unit, -self.value))

class Cooldown(ItemComponent):
    nid = 'cooldown'
    desc = "After use, item cannot be used until X turns have passed"
    expose = Type.Int
    tag = 'uses'

    def init(self, unit, item):
        item.data['cooldown'] = 0

    def available(self, unit, item) -> bool:
        return item.data['cooldown'] == 0

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.SetItemData(item, 'cooldown', self.value))

    def on_miss(self, actions, playback, unit, item, target, mode=None):
        actions.append(action.SetItemData(item, 'cooldown', self.value))

    def on_upkeep(self, unit, item):
        if item.data['cooldown'] > 0:
            action.do(action.IncItemData(item, 'cooldown', -1))

class PrfUnit(ItemComponent):
    nid = 'prf_unit'
    desc = 'Item can only be wielded by certain units'
    expose = (Type.List, Type.Unit)
    tag = 'uses'

    def available(self, unit, item) -> bool:
        return unit.nid in self.value

class PrfClass(ItemComponent):
    nid = 'prf_class'
    desc = 'Item can only be wielded by certain classes'
    expose = (Type.List, Type.Class)
    tag = 'uses'

    def available(self, unit, item) -> bool:
        return unit.klass in self.value

class PrfTag(ItemComponent):
    nid = 'prf_tags'
    desc = 'Item can only be wielded by units with certain tags'
    expose = (Type.List, Type.Tag)
    tag = 'uses'

    def available(self, unit, item) -> bool:
        return any(tag in self.value for tag in unit.tags)

class Locked(ItemComponent):
    nid = 'locked'
    desc = 'Item cannot be discarded, traded, or stolen'
    tag = 'extra'

    def locked(self, unit, item) -> bool:
        return True
