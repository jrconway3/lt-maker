from app.utilities import str_utils
from app.resources.resources import RESOURCES
from app.data.database import DB

class Validator():
    def validate(self, text, level):
        return text

class OptionValidator(Validator):
    def validate(self, text, level):
        if text.lower() in self.valid:
            return text
        return None

class Condition(Validator):
    pass

class PositiveInteger(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return int(text)
        return None

class Time(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return int(text)
        return None

class Music(Validator):
    def validate(self, text, level):
        if text in RESOURCES.music.keys():
            return text
        return None

class Sound(Validator):
    def validate(self, text, level):
        if text in RESOURCES.sfx.keys():
            return text
        return None

class Portrait(Validator):
    def validate(self, text, level):
        if text in DB.units.keys():
            return text
        elif text in RESOURCES.portraits.keys():
            return text
        return None

class ScreenPosition(Validator):
    valid_positions = ["OffscreenLeft", "FarLeft", "Left", "MidLeft", "CenterLeft", "CenterRight", "MidRight", "Right", "FarRight", "OffscreenRight"]

    def validate(self, text, level):
        if text in self.valid_positions:
            return text
        elif str_utils.is_int(text):
            return text
        elif ',' in text and len(text.split(',')) == 2 and all(str_utils.is_int(t) for t in text.split(',')):
            return text
        return None

class Slide(OptionValidator):
    valid = ["normal", "left", "right"]

class Direction(OptionValidator):
    valid = ["open", "close"]

class ExpressionList(Validator):
    valid_expressions = ["NoSmile", "Smile", "NormalBlink", "CloseEyes", "HalfCloseEyes", "OpenEyes"]

    def validate(self, text, level):
        if ',' in text:
            text = text.split(',')
        else:
            text = [text]
        for t in text:
            if t not in self.valid_expressions:
                return None
        return text

class Speaker(Validator):
    def validate(self, text, level):
        return text

class Text(Validator):
    def validate(self, text, level):
        return text

class Panorama(Validator):
    def validate(self, text, level):
        if text in RESOURCES.panoramas.keys():
            return text
        return None

class Width(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return 8 * round(int(text) / 8)
        return None

class Speed(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return text
        return None

class Color3(Validator):
    def validate(self, text, level):
        if ',' not in text:
            return None
        text = text.split(',')
        if len(text) != 3:
            return None
        if all(str_utils.is_int(t) and 0 <= int(t) <= 255 for t in text):
            return text
        return None

class Bool(OptionValidator):
    valid = ['t', 'true', '1', 'y', 'yes', 'f', 'false', '0', 'n', 'no']

class ShopFlavor(OptionValidator):
    valid = ['armory', 'vendor']

class Position(Validator):
    def validate(self, text, level):
        text = text.split(',')
        if len(text) == 1:
            text = text[0]
            if level and text in level.units.keys():
                return text
            return None
        if len(text) > 2:
            return None
        if not all(str_utils.is_int(t) for t in text):
            return None
        if level and level.tilemap:
            tilemap = RESOURCES.tilemaps.get(level.tilemap)
            x, y = text
            x = int(x)
            y = int(y)
            if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                return text
            return None
        else:
            return text
        return None

class Unit(Validator):
    def validate(self, text, level):
        if not level:
            return text
        nids = [u.nid for u in level.units]
        if text in nids:
            return text
        return None

class Group(Validator):
    def validate(self, text, level):
        if not level:
            return None
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

class GlobalUnit(Validator):
    def validate(self, text, level):
        if level:
            nids = [u.nid for u in level.units]
            if text in nids:
                return text
        if text.lower() == 'convoy':
            return text
        elif text in DB.units.keys():
            return text
        return None

class StartingGroup(Validator):
    def validate(self, text, level):
        if not level:
            return None
        if text.lower() == 'starting':
            return text
        if text.lower() in ('east', 'north', 'south', 'west'):
            return text
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

class EntryType(OptionValidator):
    valid = ['fade', 'immediate', 'warp']

class Placement(OptionValidator):
    valid = ['giveup', 'stack', 'closest', 'push']

class MovementType(OptionValidator):
    valid = ['normal', 'fade', 'immediate', 'warp']

class RemoveType(OptionValidator):
    valid = ['fade', 'immediate', 'warp']

class Script(Validator):
    valid_commands = ['hit1', 'hit2', 'crit1', 'crit2', 'miss1', 'miss2', '--', 'end']

    def validate(self, text, level):
        commands = text.split(',')
        if all(command.lower() in self.valid_commands for command in commands):
            return text
        return None

class Ability(Validator):
    def validate(self, text, level):
        if text in DB.items.keys():
            return text
        elif text in DB.skills.keys():
            return text
        return None

class Item(Validator):
    def validate(self, text, level):
        if text in DB.items.keys():
            return text
        return None

class ItemList(Validator):
    def validate(self, text, level):
        items = text.split(',')
        if all(item in DB.items.keys() for item in items):
            return text
        return None

validators = {validator.__name__: validator for validator in Validator.__subclasses__()}

def validate(var_type, text, level):
    validator = validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text, level)
    else:
        return text
