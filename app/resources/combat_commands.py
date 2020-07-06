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
    elif attr is bool:
        return True
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
    if command_nid == 'f':
        if len(split_text) == 3: 
            command_nid = 'frame'
        elif len(split_text) == 4:
            command_nid = 'dual_frame'
        elif len(split_text) == 5:
            command_nid = 'frame_with_offset'
            split_text = [split_text[0], split_text[1], split_text[2], split_text[4].split(',')]
    elif command_nid == 'of':
        command_nid = 'over_frame'
    elif command_nid == 'uf':
        command_nid = 'under_frame'
    elif command_nid == 'self_flash_white':
        command_nid = 'self_tint'
        split_text.append('248,248,248')
    elif command_nid == 'enemy_flash_white':
        command_nid = 'enemy_tint'
        split_text.append('248,248,248')
    elif command_nid == 'screen_flash_white':
        command_nid = 'screen_blend'
        split_text.append('248,248,248')
    command = get_command(command_nid)
    values = []
    if isinstance(command.attr, tuple):
        for idx, attr in enumerate(command.attr):
            value = parse_attr(attr, split_text[idx + 1])
            values.append(value)
    elif command.attr:
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
    CombatAnimationCommand('over_frame', 'Display Over Frame', (int, 'frame'), (0, None), 'frame'),
    CombatAnimationCommand('under_frame', 'Display Under Frame', (int, 'frame'), (0, None), 'frame'),
    CombatAnimationCommand('dual_frame', 'Display Dual Frame', (int, 'frame', 'frame'), (0, None, None), 'frame'),
    CombatAnimationCommand('frame_with_offset', 'Display Frame With Offset', (int, 'frame', 0, 0), (0, None, 0, 0), 'frame'),
    
    CombatAnimationCommand('sound', 'Play Sound', 'sound', None, 'sound'),
    CombatAnimationCommand('stop_sound', 'Stop Sound', 'sound', None, 'sound'),

    CombatAnimationCommand('start_hit', 'Start Normal Hit Routine', None, None, 'process'),
    CombatAnimationCommand('wait_for_hit', 'Wait for End of Normal Hit Routine', ('frame', 'frame'), (None, None), 'process'),
    CombatAnimationCommand('miss', 'Miss', None, None, 'process'),
    CombatAnimationCommand('spell', 'Cast Spell', 'effect', None, 'process'),
    CombatAnimationCommand('spell_hit', 'Spell Hit Routine', None, None, 'process'),

    CombatAnimationCommand('self_tint', 'Tint Self', (int, 'color'), (0, 248, 248, 248), 'aesthetic1'),
    CombatAnimationCommand('enemy_tint', 'Tint Enemy', (int, 'color'), (0, 248, 248, 248), 'aesthetic1'),
    CombatAnimationCommand('background_blend', 'Tint Background', (int, 'color'), (0, (248, 248, 248)), 'aesthetic1'),
    CombatAnimationCommand('foreground_blend', 'Tint Foreground', (int, 'color'), (0, (248, 248, 248)), 'aesthetic1'),
    CombatAnimationCommand('screen_blend', 'Tint Entire Screen', (int, 'color'), (0, (248, 248, 248)), 'aesthetic1'),
    CombatAnimationCommand('opacity', 'Set Opacity', int, 0, 'aesthetic1'),

    CombatAnimationCommand('platform_shake', 'Shake Platform', None, None, 'aesthetic2'),
    CombatAnimationCommand('screen_shake', 'Shake Screen', None, None, 'aesthetic2'),
    CombatAnimationCommand('hit_spark', 'Show Hit Spark', None, None, 'aesthetic2'),
    CombatAnimationCommand('crit_spark', 'Show Crit Spark', None, None, 'aesthetic2'),
    CombatAnimationCommand('darken', 'Darken Background', None, None, 'aesthetic2'),
    CombatAnimationCommand('lighten', 'Lighten Background', None, None, 'aesthetic2'),

    CombatAnimationCommand('effect', 'Show Effect On Self', 'effect', None, 'effect'),
    CombatAnimationCommand('under_effect', 'Show Effect Under Self', 'effect', None, 'effect'),
    CombatAnimationCommand('enemy_effect', 'Show Effect On Enemy', 'effect', None, 'effect'),
    CombatAnimationCommand('enemy_under_effect', 'Show Effect Under Enemy', 'effect', None, 'effect'),
    CombatAnimationCommand('clear_all_effects', 'Clear All Effects', None, None, 'effect'),

    CombatAnimationCommand('pan', 'Pan Screen', None, None, 'aesthetic3'),
    CombatAnimationCommand('blend', 'Set Frame Blending', bool, True, 'aesthetic3'),
    CombatAnimationCommand('static', 'Set Has Static Position', bool, True, 'aesthetic3'),
    CombatAnimationCommand('ignore_pan', 'Set Ignore Pan', bool, True, 'aesthetic3'),
    
    CombatAnimationCommand('start_loop', 'Start Loop', None, None, 'loop'),
    CombatAnimationCommand('end_loop', 'End Loop', None, None, 'loop'),
    CombatAnimationCommand('end_parent_loop', 'Break Parent Loop', None, None, 'loop'),
    CombatAnimationCommand('end_child_loop', 'Break All Effect Loops', None, None, 'loop')
])
    

def get_command(nid):
    print(nid)
    base = anim_commands.get(nid)
    return CombatAnimationCommand.copy(base)
