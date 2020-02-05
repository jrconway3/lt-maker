from app.data.data import data, Prefab

AI_ActionTypes = ['None', 'Attack', 'Steal', 'Interact', 'Move_to', 'Move_away_from']
AI_TargetTypes = ['None', 'Enemy', 'Ally', 'Unit', 'Position', 'Tile', 'Event']
unit_spec = ['All', 'Class', 'Tag', 'Name', 'Faction', 'ID']
event_types = ['Seize', 'Escape', 'Locked', 'Destructible', 'Hidden_Escape', 'Enemy_Seize']
AI_TargetSpecifications = [[], unit_spec, unit_spec, unit_spec, ['Starting', 'Custom'], [], event_types]
# View Range
# (Don't look | Movement*2 + Maximum Item Range | Entire Map | Custom Range (Integer))

class AIPreset(Prefab):
    def __init__(self, nid, priority):
        self.nid = nid
        self.behaviours = [AIBehaviour.DoNothing(), AIBehaviour.DoNothing(), AIBehaviour.DoNothing()]
        self.priority: int = priority

    def add_behaviour(self, behaviour):
        self.behaviours.append(behaviour)

    def set_behaviour(self, idx, behaviour):
        self.behaviours[idx] = behaviour

    def serialize_attr(self, name, value):
        if name == 'behaviours':
            value = [b.serialize() for b in value]
        else:
            value = super().serialize_attr(name, value)
        return value

    def deserialize_attr(self, name, value):
        if name == 'behaviours':
            value = [AIBehaviour.deserialize(b) for b in value]
        else:
            value = super().deserialize_attr(name, value)
        return value

class AIBehaviour(Prefab):
    def __init__(self, action: str, target: str, target_spec, view_range: int):
        self.action: str = action
        self.target: str = target
        self.target_spec = target_spec
        self.view_range: int = view_range

    @classmethod
    def DoNothing(cls):
        return cls('None', 'None', None, 0)

class AICatalog(data):
    datatype = AIPreset

    def import_data(self, fn):
        with open(fn) as fp:
            lines = [line.strip().split() for line in fp.readlines() if not line.startswith('#')]

        for line in lines:
            nid = line[0]
            priority = int(line[1])
            new_ai = AIPreset(nid, priority)

            for idx, behaviour in enumerate(line[2:]):
                action, target, view_range = behaviour.split(',')
                if ':' in target:
                    split_target = target.split(':')
                    target = split_target[0]
                    target_spec = split_target[1:]
                else:
                    target_spec = None
                new_behaviour = AIBehaviour(action, target, target_spec, int(view_range))
                new_ai.set_behaviour(idx, new_behaviour)
                
            self.append(new_ai)
