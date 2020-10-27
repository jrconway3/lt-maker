from app.utilities.data import Prefab

class EventCommand(Prefab):
    nid: str = None
    nickname: str = None
    tag: str = 'general'

    keywords: list = []
    optional_keywords: list = []
    flags: list = []

    values: list = []

    def __init__(self, values=None):
        self.values = values or []

    def save(self):
        return self.nid, self.values

    def to_plain_text(self):
        return ';'.join([self.nid] + self.values)

class Wait(EventCommand):
    nid = "wait"
    tag = "general"

    keywords = ['Time']

class Music(EventCommand):
    nid = "music"
    nickname = "m"
    tag = "sound"

    keywords = ['Music']

class Sound(EventCommand):
    nid = "sound"
    tag = "sound"

    keywords = ['Sound']

class AddPortrait(EventCommand):
    nid = "add_portrait"
    nickname = "u"
    tag = "dialogue"

    keywords = ['Portrait', 'ScreenPosition']
    optional_keywords = ['Slide', 'ExpressionList']
    flags = ["mirror", "low_priority", "immediate", "no_block"]

class RemovePortrait(EventCommand):
    nid = "remove_portrait"
    nickname = "r"
    tag = "dialogue"

    keywords = ['Portrait']
    flags = ["immediate", "no_block"]

class MovePortrait(EventCommand):
    nid = "move_portrait"
    nickname = "mov"
    tag = "dialogue"

    keywords = ['Portrait', 'ScreenPosition']
    flags = ["immediate", "no_block"]

class BopPortrait(EventCommand):
    nid = "bop_portrait"
    nickname = "bop"
    tag = "dialogue"

    keywords = ['Portrait']
    flags = ["no_block"]

class Expression(EventCommand):
    nid = "expression"
    nickname = "e"
    tag = "dialogue"

    keywords = ['Portrait', 'ExpressionList']

class Speak(EventCommand):
    nid = "speak"
    tag = "dialogue"

    keywords = ['Speaker', 'Text']
    optional_keywords = ['ScreenPosition', 'Width']

class Transition(EventCommand):
    nid = "transition"
    nickname = "t"
    tag = "background"

    optional_keywords = ['Direction', 'Speed', 'Color3']

class Background(EventCommand):
    # Also does remove background
    nid = "change_background"
    nickname = "b"
    tag = "background"

    keywords = ['Panorama']
    flags = ["keep_portraits"]

def restore_command(dat):
    nid, values = dat
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == nid:
            copy = command(values)
            return copy
    return None

def parse_text(text):
    arguments = text.split(';')
    command_nid = arguments[0]
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == command_nid or command.nickname == command_nid:
            copy = command(arguments[1:])
            return copy
    return None
