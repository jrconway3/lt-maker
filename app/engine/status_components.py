from app.engine.status_system import StatusComponent

# status plugins
class Unselectable(StatusComponent):
    nid = 'unselectable'
    desc = "Unit cannot be selected"

    def can_select(unit) -> bool:
        return False

class IgnoreAlliances(StatusComponent):
    nid = 'ignore_alliances'
    desc = "Unit will treat all units as enemies"

    def check_ally(unit1, unit2) -> bool:
        return False

    def check_enemy(unit1, unit2) -> bool:
        return True
