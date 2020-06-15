from app.data.data import Data

class CombatAnimationCommand():
    def __init__(self, nid=None, name='', attr=bool, value=True, tag=None):
        self.nid: str = nid
        self.name: str = name
        self.attr = attr
        self.value = value
        self.tag = tag

    @classmethod
    def copy(cls, other):
        return cls(other.nid, other.name, other.attr, other.value, other.tag)

    def serialize(self):
        return self.nid, self.value

def parse_attr(attr, text: str):
    if attr is None:
        return None
    elif attr is int:
        return int(text)
    elif attr == 'color':
        return tuple(int(_) for _ in text.split(','))
    elif attr == 'frame':
        return text
    elif attr == 'sound':
        return text

def parse_text(split_text: list) -> CombatAnimationCommand:
    command_nid = split_text[0]
    if command_nid == 'f' or command_nid == 'of': 
        command_nid = 'frame'
    command = get_command(command_nid)
    values = []
    if isinstance(command.attr, tuple):
        for idx, attr in enumerate(command.attr):
            value = parse_attr(attr, split_text[idx + 1])
            values.append(value)
    else:
        value = parse_attr(command.attr, split_text[1])
        values.append(value)
    if len(values) == 0:
        pass
    elif len(values) == 1:
        command.value = values[0]
    elif len(values) > 1:
        command.value = tuple(values)
    return command

anim_commands = Data([
    CombatAnimationCommand('frame', 'Display Frame', (int, 'frame'), (0, None), 'frame'),
    CombatAnimationCommand('wait', 'Wait', int, 0, 'frame'),
    
    CombatAnimationCommand('sound', 'Play Sound', 'sound', None, 'sound'),

    CombatAnimationCommand('start_hit', 'Start Hit Routine', None, None, 'process'),
    CombatAnimationCommand('wait_for_hit', 'Wait for End of Hit Routine', 'frame', None, 'process'),
    CombatAnimationCommand('miss', 'Miss', None, None, 'process'),

    CombatAnimationCommand('enemy_flash_white', 'Flash Enemy White', int, 0, 'aesthetic1'),
    CombatAnimationCommand('screen_flash_white', 'Flash Screen White', int, 0, 'aesthetic1'),
    CombatAnimationCommand('foreground_blend', 'Blend Foreground', (int, 'color'), (0, (248, 248, 248)), 'aesthetic1'),
    CombatAnimationCommand('platform_shake', 'Shake Platform', None, None, 'aesthetic2'),
    CombatAnimationCommand('screen_shake', 'Shake Screen', None, None, 'aesthetic2'),
    CombatAnimationCommand('hit_spark', 'Show Hit Spark', None, None, 'aesthetic2'),
    CombatAnimationCommand('crit_spark', 'Show Crit Spark', None, None, 'aesthetic2'),
])
    

def get_command(nid):
    print(nid)
    base = anim_commands.get(nid)
    return CombatAnimationCommand.copy(base)
