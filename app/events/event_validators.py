from app.utilities import str_utils
from app.resources.resources import RESOURCES
from app.data.database import DB

class Validator():
    desc = ""
    
    def validate(self, text, level):
        return text

class OptionValidator(Validator):
    valid = []

    @property
    def desc(self) -> str:
        return "must be one of (`%s`)" % '`, `'.join(self.valid)

    def validate(self, text, level):
        if text.lower() in self.valid:
            return text
        return None

class Condition(Validator):
    desc = "must be a valid Python expression to evaluate."

class Nid(Validator):
    """
    Any nid will do, because we cannot know what
    objects will have been created
    """
    pass

class Integer(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return int(text)
        return None

class PositiveInteger(Validator):
    desc = "must be a positive whole number"
    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return int(text)
        return None

class String(Validator):
    """
    Any string will do
    """
    pass

class Time(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return int(text)
        return None

class Music(Validator):
    def validate(self, text, level):
        if text in RESOURCES.music.keys():
            return text
        elif text == 'None':
            return text
        return None

class Sound(Validator):
    def validate(self, text, level):
        if text in RESOURCES.sfx.keys():
            return text
        return None

class PhaseMusic(OptionValidator):
    valid = ['player_phase', 'enemy_phase', 'other_phase', 'enemy2_phase',
             'player_battle', 'enemy_battle', 'other_battle', 'enemy2_battle']

class PortraitNid(Validator):
    def validate(self, text, level):
        if text in RESOURCES.portraits.keys():
            return text
        return None

class Portrait(Validator):
    desc = "can be a unit's nid, a portrait's nid, or one of (`{unit}`, `{unit1}`, `{unit2}`)."

    def validate(self, text, level):
        if text in DB.units.keys():
            return text
        elif text in RESOURCES.portraits.keys():
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return text
        return None

class AI(Validator):
    def validate(self, text, level):
        if text in DB.ai.keys():
            return text
        return None

class Team(Validator):
    def validate(self, text, level):
        if text in DB.teams:
            return text
        return None

class Tag(Validator):
    def validate(self, text, level):
        if text in DB.tags.keys():
            return text
        return None

class ScreenPosition(Validator):
    valid_positions = ["OffscreenLeft", "FarLeft", "Left", "MidLeft", "CenterLeft", "CenterRight", "MidRight", "Right", "FarRight", "OffscreenRight"]

    desc = "determines where to add the portrait to the screen. Available options are (`OffscreenLeft`, `FarLeft`, `Left`, `MidLeft`, `MidRight`, `Right`, `FarRight`, `OffscreenRight`). Alternatively, specify a position in pixels (`x,y`) for the topleft of the portrait. If the portrait is placed on the left side of the screen to start, it will be facing right, and vice versa."

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

class Orientation(OptionValidator):
    valid = ["h", "horiz", "horizontal", "v", "vert", "vertical"]

class ExpressionList(Validator):
    valid_expressions = ["NoSmile", "Smile", "NormalBlink", "CloseEyes", "HalfCloseEyes", "OpenEyes"]
    desc = "expects a comma-delimited list of expressions. Valid expressions are: (`NoSmile`, `Smile`, `NormalBlink`, `CloseEyes`, `HalfCloseEyes`, `OpenEyes`). Example: `Smile,CloseEyes`"

    def validate(self, text, level):
        text = text.split(',')
        for t in text:
            if t not in self.valid_expressions:
                return None
        return text

class DialogVariant(OptionValidator):
    valid = ["thought_bubble", "noir", "hint", "narration", "narration_top", "cinematic"]

class StringList(Validator):
    desc = "must be delimited by commas. For example: `Water,Earth,Fire,Air`"

    def validate(self, text, level):
        text = text.split(',')
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
    desc = "is measured in pixels"

    def validate(self, text, level):
        if str_utils.is_int(text):
            return 8 * round(int(text) / 8)
        return None

class Speed(Validator):
    desc = "is measured in milliseconds"

    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return text
        return None

class Color3(Validator):
    desc = "uses 0-255 for color channels. Example: `128,160,136`"

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
    desc = "accepts a valid `(x, y)` position. You use a unit's nid to use their position. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`, `{position}`)"

    def validate(self, text, level):
        text = text.split(',')
        if len(text) == 1:
            text = text[0]
            if level and text in level.units.keys():
                return text
            elif text in ('{unit}', '{unit1}', '{unit2}', '{position}'):
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

class PositionOffset(Validator):
    desc = "accepts a valid `(x, y)` position offset."

    def validate(self, text, level):
        text = text.split(',')
        if len(text) != 2:
            return None
        if not all(str_utils.is_int(t) for t in text):
            return None
        return text

class Size(Validator):
    desc = "must be in the format `x,y`. Example: `64,32`"

    def validate(self, text, level):
        text = text.split(',')
        if len(text) > 2:
            return None
        if not all(str_utils.is_int(t) and int(t) > 0 for t in text):
            return None
        return text

class Unit(Validator):
    desc = "accepts a unit's nid. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`)."
    
    def validate(self, text, level):
        if not level:
            return text
        nids = [u.nid for u in level.units]
        if text in nids:
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return True
        return None

class Group(Validator):
    def validate(self, text, level):
        if not level:
            return None
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

class StartingGroup(Validator):
    desc = "accepts a unit group's nid. Alternatively, can be `starting` to use the unit's starting positions in the level."

    def validate(self, text, level):
        if not level:
            return None
        if ',' in text and len(text.split(',')) == 2:
            if all(str_utils.is_int(t) for t in text.split(',')):
                return text
            else:
                return None
        if text.lower() == 'starting':
            return text
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

class UniqueUnit(Validator):
    def validate(self, text, level):
        if text in DB.units.keys():
            return text
        return None

class GlobalUnit(Validator):
    desc = "accepts a unit's nid. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`) or `convoy` where appropriate."

    def validate(self, text, level):
        if level:
            nids = [u.nid for u in level.units]
            if text in nids:
                return text
        if text.lower() == 'convoy':
            return text
        elif text in DB.units.keys():
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return True
        return None

class CardinalDirection(OptionValidator):
    valid = ['north', 'east', 'west', 'south']
    
class EntryType(OptionValidator):
    valid = ['fade', 'immediate', 'warp', 'swoosh']

class Placement(OptionValidator):
    valid = ['giveup', 'stack', 'closest', 'push']

class MovementType(OptionValidator):
    valid = ['normal', 'fade', 'immediate', 'warp', 'swoosh']

class RemoveType(OptionValidator):
    valid = ['fade', 'immediate', 'warp', 'swoosh']

class RegionType(OptionValidator):
    valid = ['normal', 'event', 'status', 'formation']

class Weather(OptionValidator):
    valid = ["rain", "sand", "snow", "fire", "light", "dark", "smoke"]

class CombatScript(Validator):
    valid_commands = ['hit1', 'hit2', 'crit1', 'crit2', 'miss1', 'miss2', '--', 'end']
    desc = "specifies the order and type of actions in combat. Valid actions: (`hit1`, `hit2`, `crit1`, `crit2`, `miss1`, `miss2`, `--`, `end`)."

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
    desc = "accepts a comma-delimited list of item nids. Example: `Iron Sword,Iron Lance,Iron Bow`"

    def validate(self, text, level):
        items = text.split(',')
        if all(item in DB.items.keys() for item in items):
            return text
        return None

class StatList(Validator):
    desc = "accepts a comma-delimited list of pairs of stat nids and stat changes. For example, `STR,2,SPD,-3` to increase STR by 2 and decrease SPD by 3."

    def validate(self, text, level):
        s_l = text.split(',')
        if len(s_l)%2 != 0:  # Must be divisible by 2
            return None
        for idx in range(len(s_l)//2):
            stat_nid = s_l[idx*2]
            stat_value = s_l[idx*2 + 1]
            if stat_nid not in DB.stats.keys():
                return None
            elif not str_utils.is_int(stat_value):
                return None
        return text

class Skill(Validator):
    def validate(self, text, level):
        if text in DB.skills.keys():
            return text
        return None

class Party(Validator):
    def validate(self, text, level):
        if text in DB.parties.keys():
            return text
        return None

class Faction(Validator):
    def validate(self, text, level):
        if text in DB.factions.keys():
            return text
        return None

class Klass(Validator):
    def validate(self, text, level):
        if text in DB.classes.keys():
            return text
        return None

class Lore(Validator):
    def validate(self, text, level):
        if text in DB.lore.keys():
            return text
        return None

class WeaponType(Validator):
    def validate(self, text, level):
        if text in DB.weapons.keys():
            return text
        return None

class Layer(Validator):
    def validate(self, text, level):
        tilemap_prefab = RESOURCES.tilemaps.get(level.tilemap)
        if text in tilemap_prefab.layers.keys():
            return text
        return None

class LayerTransition(OptionValidator):
    valid = ['fade', 'immediate']

class MapAnim(Validator):
    def validate(self, text, level):
        if text in RESOURCES.animations.keys():
            return text
        return None

class Tilemap(Validator):
    def validate(self, text, level):
        if text in RESOURCES.tilemaps.keys():
            return text
        return None

class Event(Validator):
    desc = "accepts the name of an event. Will run the event appropriate for the level if more than one event with the same name exists."

    def validate(self, text, level):
        for event in DB.events:
            if event.name == text and (not event.level_nid or not level or event.level_nid == level.nid):
                return text
        return None

validators = {validator.__name__: validator for validator in Validator.__subclasses__()}
option_validators = {validator.__name__: validator for validator in OptionValidator.__subclasses__()}

def validate(var_type, text, level):
    validator = validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text, level)
    validator = option_validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text, level)
    else:
        return text

def get(keyword) -> Validator:
    if keyword in validators:
        return validators[keyword]
    elif keyword in option_validators:
        return option_validators[keyword]
    return None
