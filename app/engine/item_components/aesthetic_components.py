from app.data.item_components import ItemComponent
from app.data.components import Type

class MapHitColor(ItemComponent):
    nid = 'map_hit_color'
    desc = "Changes the color that appears on the unit when hit"
    tag = 'aesthetic'

    expose = Type.Color4
    value = (255, 255, 255, 128)

    def on_hit(self, actions, playback, unit, item, target, mode):
        playback.append(('unit_tint', target, self.value))

    def on_crit(self, actions, playback, unit, item, target, mode):
        playback.append(('unit_tint', target, self.value))

class MapHitSFX(ItemComponent):
    nid = 'map_hit_sfx'
    desc = "Changes the sound the item will make on hit"
    tag = 'aesthetic'

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, mode):
        playback.append(('hit_sound', self.value))

    def on_crit(self, actions, playback, unit, item, target, mode):
        playback.append(('hit_sound', self.value))

class MapCastSFX(ItemComponent):
    nid = 'map_cast_sfx'
    desc = "Adds a sound to the item on cast"
    tag = 'aesthetic'

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, mode):
        playback.append(('cast_sound', self.value))

    def on_crit(self, actions, playback, unit, item, target, mode):
        playback.append(('cast_sound', self.value))

    def on_miss(self, actions, playback, unit, item, target, mode):
        playback.append(('cast_sound', self.value))

class Warning(ItemComponent):
    nid = 'warning'
    desc = "Yellow warning sign appears above wielder's head"
    tag = 'aesthetic'

    # TODO: Doesn't actually hook into anything yet!
    def warning(self, unit, item):
        return True
