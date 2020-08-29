from app.data.item_components import ItemComponent, Type

class MapHitColor(ItemComponent):
    nid = 'map_hit_color'
    desc = "Changes the color that appears on the unit when hit"
    tag = 'aesthetic'

    expose = Type.Color4
    value = (255, 255, 255, 128)

    def on_hit(self, actions, playback, unit, item, target, mode=None):
        playback.append(('unit_tint', target, self.value))

    def on_crit(self, actions, playback, unit, item, target, mode=None):
        playback.append(('unit_tint', target, self.value))
