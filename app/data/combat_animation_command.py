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
        return cls(other.nid, other.name, other.attr, other.value)

    def serialize(self):
        return self.nid, self.value

anim_commands = Data([
    CombatAnimationCommand('frame', '<b>Display Frame</b>', (int, 'frame'), (0, None), 'frame'),
    CombatAnimationCommand('wait', '<b>Wait</b>', int, 0, 'frame'),
    
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
    base = anim_commands.get(nid)
    return CombatAnimationCommand.copy(base)
