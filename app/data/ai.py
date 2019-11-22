from app.data.data import data

AI_ActionTypes = ['Move', 'Attack Units', 'Steal', 'Attack Tiles', 'Interact']
AI_TargetTypes = ['Allies', 'Enemies', 'HP Tiles', 'Event Tiles', 'Specific Unit']

# View Range
# (Don't look | Movement*2 + Maximum Item Range | Entire Map | Custom Range (Integer))

class AIPreset(object):
    def __init__(self, nid, actions, targets1, targets2, view_range, priority):
        self.nid = nid
        self.actions = actions
        self.targets1 = targets1
        self.target_unit1 = None
        self.targets2 = targets2
        self.target_unit2 = None
        self.view_range = view_range
        self.priority: int = priority

def binary_convert(binary, ty):
    new_list = []
    for idx in range(len(ty)):
        test_idx = idx + 1
        bin_value = 2**test_idx
        if binary % test_idx == 0:
            new_list.append(ty[idx])
            binary -= bin_value
    return new_list

class AICatalog(data):
    def import_data(self, fn):
        with open(fn) as fp:
            lines = [line.strip().split() for line in fp.readlines() if not line.startswith('#')]

        for line in lines:
            nid = line[0]
            actions = binary_convert(line[1], AI_ActionTypes)
            targets1 = binary_convert(line[2], AI_TargetTypes)
            targets2 = binary_convert(line[3], AI_TargetTypes)
            view_range = int(line[4])
            priority = int(line[5])

            ai = AIPreset(nid, actions, targets1, targets2, view_range, priority)
            self.append(ai)

# Testing
# Run "python -m app.data.ai" from main directory
if __name__ == '__main__':
    print(binary_convert(16, AI_ActionTypes))
    print(binary_convert(3, AI_ActionTypes))
    print(binary_convert(19, AI_ActionTypes))
