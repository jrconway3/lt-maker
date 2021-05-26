from app.resources.resources import RESOURCES
from app.data.database import DB

class BattleAnimation():
    def __init__(self, anim_prefab, unit, item):
        self.anim_prefab = anim_prefab
        self.unit = unit
        self.item = item

        self.current_pose = None
        self.current_palette = None

        self.state = 'inert'

def get_battle_anim(unit, item) -> BattleAnimation:
    class_obj = DB.classes.get(unit.klass)
    combat_anim_nid = class_obj.combat_anim_nid
    if unit.variant:
        combat_anim_nid += unit.variant
    res = RESOURCES.combat_anims.get(combat_anim_nid)
    if not res:  # Try without unit variant
        res = RESOURCES.combat_anims.get(class_obj.combat_anim_nid)
    if not res:
        return None

    battle_anim = BattleAnimation(res, unit, item)
    return battle_anim
