from app.utilities.data import Data, Prefab

AI_ActionTypes = ['None', 'Attack', 'Steal', 'Interact', 'Move_to', 'Move_away_from']
AI_TargetTypes = ['None', 'Enemy', 'Ally', 'Unit', 'Position', 'Tile', 'Event']
unit_spec = ['All', 'Class', 'Tag', 'Name', 'Faction', 'ID']
event_types = ['Seize', 'Escape', 'Locked', 'Destructible', 'Hidden_Escape', 'Enemy_Seize']
AI_TargetSpecifications = [[], unit_spec, unit_spec, unit_spec, ['Starting', 'Custom'], [], event_types]
# View Range
# (Don't look | Movement*2 + Maximum Item Range | Entire Map | Custom Range (Integer))

class AIPrefab(Prefab):
    def __init__(self, nid, priority):
        self.nid = nid
        self.behaviours = [AIBehaviour.DoNothing(), AIBehaviour.DoNothing(), AIBehaviour.DoNothing()]
        self.priority: int = priority

    def add_behaviour(self, behaviour):
        self.behaviours.append(behaviour)

    def set_behaviour(self, idx, behaviour):
        self.behaviours[idx] = behaviour

    def save_attr(self, name, value):
        if name == 'behaviours':
            value = [b.save() for b in value]
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'behaviours':
            value = [AIBehaviour.restore(b) for b in value]
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls(None, 0)

class AIBehaviour(Prefab):
    def __init__(self, action: str, target: str, target_spec, view_range: int):
        self.action: str = action
        self.target: str = target
        self.target_spec = target_spec
        self.view_range: int = view_range

    @classmethod
    def DoNothing(cls):
        return cls('None', 'None', None, 0)

    @classmethod
    def default(cls):
        return cls.DoNothing()

class AICatalog(Data):
    datatype = AIPrefab
