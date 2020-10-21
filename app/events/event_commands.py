from app.utilities import str_utils
from app.resources.resources import RESOURCES
from app.data.database import DB

class Validator():
    def validate(self, text):
        return text

class Time(Validator):
    def validate(self, text):
        if str_utils.is_int(text):
            return int(text)
        return None

class Music(Validator):
    def validate(self, text):
        if text in RESOURCES.music.keys():
            return text
        return None

class Sound(Validator):
    def validate(self, text):
        if text in RESOURCES.sfx.keys():
            return text
        return None

class Portrait(Validator):
    def validate(self, text):
        if text in DB.units.keys():
            return text
        elif text in RESOURCES.portraits.keys():
            return text
        return None

class ScreenPosition(Validator):
    valid_positions = ["OffscreenLeft", "FarLeft", "Left", "CenterLeft", "CenterRight", "Right", "FarRight", "OffscreenRight"]

    def validate(self, text):
        if text in self.valid_positions:
            return text
        elif str_utils.is_int(text):
            return text
        elif ',' in text and len(text.split(',')) == 2 and all(str_utils.is_int(t) for t in text.split(',')):
            return text
        return None

class ExpressionList(Validator):
    valid_expressions = ["NoSmile", "Smile", "NormalBlink", "CloseEyes", "HalfCloseEyes", "OpenEyes"]

    def validate(self, text):
        if ',' in text:
            text = text.split(',')
        else:
            text = [text]
        for t in text:
            if t not in self.valid_expressions:
                return None
        return text

class Speaker(Validator):
    def validate(self, text):
        return text

class Text(Validator):
    def validate(self, text):
        return text

class Panorama(Validator):
    def validate(self, text):
        if text in RESOURCES.panoramas.keys():
            return text
        return None

class Width(Validator):
    def validate(self, text):
        if str_utils.is_int(text):
            return 8 * round(int(text) / 8)
        return None

class Speed(Validator):
    def validate(self, text):
        if str_utils.is_int(text) and int(text) > 0:
            return text
        return None

class Color3(Validator):
    def validate(self, text):
        if ',' not in text:
            return None
        text = text.split(',')
        if len(text) != 3:
            return None
        if all(str_utils.is_int(t) and 0 <= int(t) <= 255 for t in text):
            return text
        return None

class EventCommand():
    nid: str
    nickname: str = None
    tag: str

    keywords: list
    optional_keywords: list
    flags: list

    values: list

class Wait(EventCommand):
    nid = "wait"
    tag = "general"

    keywords = [Time]

    def run(self, event):
        time = self.values[0]
        event.wait(time)

class Music(EventCommand):
    nid = "music"
    nickname = "m"
    tag = "sound"

    keywords = [Music]

    def run(self, event):
        music = self.values[0]
        SOUNDTHREAD.fade_in(music)

class Sound(EventCommand):
    nid = "sound"
    tag = "sound"

    keywords = [Sound]

    def run(self, event):
        sound = self.values[0]
        SOUNDTHREAD.play_sound(sound)

class AddPortrait(EventCommand):
    nid = "add_portrait"
    nickname = "u"
    tag = "dialogue"

    keywords = [Portrait, ScreenPosition]
    optional_keywords = [ExpressionList]
    flags = ["mirror", "low_priority", "immediate", "no_block"]

class RemovePortrait(EventCommand):
    nid = "remove_portrait"
    nickname = "r"
    tag = "dialogue"

    keywords = [Portrait]
    flags = ["immediate", "no_block"]

class MovePortrait(EventCommand):
    nid = "move_portrait"
    nickname = "mov"
    tag = "dialogue"

    keywords = [Portrait, ScreenPosition]
    flags = ["immediate", "no_block"]

class BopPortrait(EventCommand):
    nid = "bop_portrait"
    nickname = "bop"
    tag = "dialogue"

    keywords = [Portrait]
    flags = ["no_block"]

class Expression(EventCommand):
    nid = "expression"
    nickname = "e"
    tag = "dialogue"

    keywords = [Portrait, ExpressionList]

class Speak(EventCommand):
    nid = "speak"
    tag = "dialogue"

    keywords = [Speaker, Text]
    optional_keywords = [ScreenPosition, Width]

class Transition(EventCommand):
    nid = "transition"
    nickname = "t"
    tag = "background"

    optional_keywords = [Speed, Color3]

class Background(EventCommand):
    # Also does remove background
    nid = "change_background"
    nickname = "b"
    tag = "background"

    keywords = [Panorama]
    flags = ["keep_portraits"]
