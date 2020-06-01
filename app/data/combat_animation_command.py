from app.data.data import Data

class CombatAnimationCommand():
    def __init__(self, nid=None, name='', attr=bool, value=True):
        self.nid: str = nid
        self.name: str = name
        self.attr = attr
        self.value = value

    @classmethod
    def copy(cls, other):
        return cls(other.nid, other.name, other.attr, other.value)

    def serialize(self):
        return self.nid, self.value

anim_commands = Data([
    CombatAnimationCommand('frame', '<b>Display Frame</b>', (int, 'frame'), (0, None)),
    CombatAnimationCommand('wait', '<b>Wait</b>', int, 0),
    
    CombatAnimationCommand('sound', 'Play Sound', 'sound', None),

    CombatAnimationCommand('start_hit', 'Start Hit Routine', None),
    CombatAnimationCommand('wait_for_hit', 'Wait for End of Hit Routine', 'frame', None),
    CombatAnimationCommand('miss', 'Miss', None),

    CombatAnimationCommand('enemy_flash_white', 'Flash Enemy White', int, 0),
    CombatAnimationCommand('screen_flash_white', 'Flash Screen White', int, 0),
    CombatAnimationCommand('foreground_blend', 'Blend Foreground', (int, 'color'), (0, (248, 248, 248))),
    CombatAnimationCommand('platform_shake', 'Shake Platform', None),
    CombatAnimationCommand('screen_shake', 'Shake Screen', None),
    CombatAnimationCommand('hit_spark', 'Show Hit Spark', None),
    CombatAnimationCommand('crit_spark', 'Show Crit Spark', None),
])
    

def get_command(nid):
    base = anim_commands.get(nid)
    return CombatAnimationCommand.copy(base)
