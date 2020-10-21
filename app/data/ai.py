from app.utilities.data import Data, Prefab

AI_ActionTypes = ['None', 'Attack', 'Support', 'Steal', 'Interact', 'Move_to', 'Move_away_from']
AI_TargetTypes = ['None', 'Enemy', 'Ally', 'Unit', 'Position', 'Event']
unit_spec = ['All', 'Class', 'Tag', 'Name', 'Faction', 'ID']
event_types = ['Seize', 'Escape', 'Locked', 'Destructible', 'Hidden_Escape', 'Enemy_Seize']
AI_TargetSpecifications = [[], unit_spec, unit_spec, unit_spec, event_types, AI_TargetTypes, AI_TargetTypes]
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
    def __init__(self, action: str, target, view_range: int):
        self.action: str = action
        self.target = target
        self.view_range: int = view_range

    @classmethod
    def DoNothing(cls):
        return cls('None', 'None', 0)

    @classmethod
    def default(cls):
        return cls.DoNothing()

    def save(self):
        s_dict = {}
        s_dict['action'] = self.save_attr('action', self.action)
        s_dict['target'] = self.save_attr('target', self.target)
        s_dict['view_range'] = self.save_attr('view_range', self.view_range)
        return s_dict

class AICatalog(Data):
    datatype = AIPrefab
