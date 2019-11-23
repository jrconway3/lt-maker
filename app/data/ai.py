from app.data.data import data

AI_ActionTypes = ['None', 'Attack', 'Steal', 'Interact', 'Move_to', 'Move_away_from']
AI_TargetTypes = ['None', 'Enemy', 'Ally', 'Unit', 'Specific_Unit', 'Position', 'Tile', 'Event']
# View Range
# (Don't look | Movement*2 + Maximum Item Range | Entire Map | Custom Range (Integer))

class AIPreset(object):
    def __init__(self, nid, priority):
        self.nid = nid
        self.behaviours = []
        self.priority: int = priority

    def add_behaviour(self, behaviour):
        self.behaviours.append(behaviour)

class AIBehaviour(object):
    def __init__(self, action, target, view_range):
        self.action = action
        self.target = target
        self.view_range: int = view_range

class AICatalog(data):
    def import_data(self, fn):
        with open(fn) as fp:
            lines = [line.strip().split() for line in fp.readlines() if not line.startswith('#')]

        for line in lines:
            nid = line[0]
            priority = int(line[1])
            new_ai = AIPreset(nid, priority)

            for behaviour in line[2:]:
                action, target, view_range = behaviour.split(',')
                if ':' in target:
                    split_target = target.split(':')
                    target = tuple(split_target)
                new_behaviour = AIBehaviour(action, target, int(view_range))
                new_ai.add_behaviour(new_behaviour)
                
            self.append(new_ai)
