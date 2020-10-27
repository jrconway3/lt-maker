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

class Slide(Validator):
    valid_slides = ["Normal", "Left", "Right"]

    def validate(self, text):
        if text in self.valid_slides:
            return text
        return None

class Direction(Validator):
    valid_directions = ["Open", "Close", "open", "close"]

    def validate(self, text):
        if text in self.valid_directions:
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

class Bool(Validator):
    valid_bools = ['t', 'true', '1', 'y', 'yes', 'f', 'false', '0', 'n', 'no']

    def validate(self, text):
        if text.lower() in self.valid_bools:
            return text
        return None

class Position(Validator):
    def validate(self, text):
        if ',' not in text:
            return None
        text = text.split(',')
        if len(text) != 2:
            return None
        if all(str_utils.is_int(t) and 0 <= int(t) <= 1024 for t in text):
            return text
        return None

validators = {validator.__name__: validator for validator in Validator.__subclasses__()}

def validate(var_type, text):
    validator = validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text)
    else:
        return text
