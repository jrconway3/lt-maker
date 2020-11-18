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

    def has_unit_spec(self, spec_type, spec_nid) -> bool:
        for behaviour in self.behaviours:
            if behaviour.has_unit_spec(spec_type, spec_nid):
                return True
        return False

    def change_unit_spec(self, spec_type, old_nid, new_nid):
        for behaviour in self.behaviours:
            behaviour.change_unit_spec(spec_type, old_nid, new_nid)

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

    def has_unit_spec(self, spec_type, spec_nid):
        if self.target[0] in ('Enemy', "Ally", "Unit"):
            if len(self.target[1]) == 2:
                if self.target[1][0] == spec_type and self.target[1][1] == spec_nid:
                    return True
        return False

    def change_unit_spec(self, spec_type, old_nid, new_nid):
        if self.target[0] in ('Enemy', "Ally", "Unit"):
            if len(self.target[1]) == 2:
                if self.target[1][0] == spec_type and self.target[1][1] == old_nid:
                    self.target[1][1] = new_nid

class AICatalog(Data):
    datatype = AIPrefab
