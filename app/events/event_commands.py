from app.utilities.data import Prefab

tags = ('Flow Control', 'Music/Sound', 'Portrait', 'Background/Foreground',
        'Dialogue/Text', 'Cursor/Camera', 
        'Level-wide Unlocks and Variables', 'Game-wide Unlocks and Variables',
        'Tilemap', 'Region', 'Add/Remove/Interact with Units', 'Modify Unit Properties', 
        'Unit Groups', 'Miscellaneous', 'Hidden')

class EventCommand(Prefab):
    nid: str = None
    nickname: str = None
    tag: str = 'general'
    desc: str = ''

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

    def __repr__(self):
        return self.to_plain_text()

class Comment(EventCommand):
    nid = "comment"
    nickname = '#'
    tag = "Flow Control"
    desc = \
        """
**Lines** starting with '#' will be ignored.
        """

    def to_plain_text(self):
        return self.values[0]

class If(EventCommand):
    nid = "if"
    tag = "Flow Control"
    desc = \
        """
If the _Condition_ returns true, the block under this command will be executed. If it returns false, the script will search for the next **elif**, **else**, or **end** command before proceeding. If it is not a valid Python expression, the result will be treated as false.

Remember to end your **if** blocks with **end**.

The indentation is not required, but is recommended for organization of the conditional blocks.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

    keywords = ['Condition']

class Elif(EventCommand):
    nid = "elif"
    tag = "Flow Control"
    desc = \
        """
Works exactly like the **if** statement, but is called only if the previous **if** or **elif** returned false.

In the following example, the **elif** will only be processed if `if;game.check_dead('Eirika')` return false.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

    keywords = ['Condition']

class Else(EventCommand):
    nid = "else"
    tag = "Flow Control"
    desc = \
        """
Defines a block to be executed only if the previous **if** or **elif** returned false.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

class End(EventCommand):
    nid = "end"
    tag = "Flow Control"
    desc = \
        """
Ends a conditional block. Refer to the **if** command for more information.
        """

class Break(EventCommand):
    nid = "break"
    tag = "Flow Control"
    desc = \
        """
Immediately ends the current event.
        """


class Wait(EventCommand):
    nid = "wait"
    tag = "Flow Control"
    desc = \
        """
Pauses the execution of the script for _Time_ milliseconds.

Often used after a scene transition, cursor movement, or reinforcements to give the player a chance to take in the scene.
        """

    keywords = ['Time']

class EndSkip(EventCommand):
    nid = "end_skip"
    tag = "Flow Control"
    desc = \
        """
If the player was skipping through the event script, stop the skip here. Used to prevent a single skip from skipping through an entire event.
        """

class Music(EventCommand):
    nid = "music"
    nickname = "m"
    tag = "Music/Sound"
    desc = \
        """
Fades in _Music_ over the course of _Time_ milliseconds. Fade in defaults to 400 milliseconds.
        """

    keywords = ['Music']
    optional_keywords = ['Time']  # How long to fade in (default 400)

class MusicClear(EventCommand):
    nid = "music_clear"
    tag = "Music/Sound"

    desc = \
        """
Fades out the currently playing song over the course of _Time_ milliseconds. Also clears the entire song stack. Fade out defaults to 400 milliseconds.
        """

    optional_keywords = ['Time']  # How long to fade out

class Sound(EventCommand):
    nid = "sound"
    tag = "Music/Sound"

    desc = \
        """
Plays the _Sound_ once.
        """

    keywords = ['Sound']

class ChangeMusic(EventCommand):
    nid = 'change_music'
    tag = 'Music/Sound'

    desc = \
        """
Changes the phase theme music. For instance, you could use this command to change the player phase theme halfway through the chapter.
        """

    keywords = ['PhaseMusic', 'Music']

class AddPortrait(EventCommand):
    nid = "add_portrait"
    nickname = "u"
    tag = "Portrait"

    desc = \
        """
Adds a portrait to the screen.

Extra flags:

1. _mirror_: Portrait will face opposite expected direction.
2. _low_priority_: Portrait will appear behind all other portraits on the screen.
3. _immediate_: Portrait will not fade in.
4. _no_block_: Portrait will fade in, but will not pause execution of event script while doing so.
        """

    keywords = ['Portrait', 'ScreenPosition']
    optional_keywords = ['Slide', 'ExpressionList']
    flags = ["mirror", "low_priority", "immediate", "no_block"]

class MultiAddPortrait(EventCommand):
    nid = "multi_add_portrait"
    nickname = "uu"
    tag = "Portrait"

    desc = \
        """
Adds more than one portrait to the screen at the same time. Accepts 2-4 portraits and their associated _ScreenPosition_ as input.
        """

    keywords = ['Portrait', 'ScreenPosition', 'Portrait', 'ScreenPosition']
    optional_keywords = ['Portrait', 'ScreenPosition', 'Portrait', 'ScreenPosition']

class RemovePortrait(EventCommand):
    nid = "remove_portrait"
    nickname = "r"
    tag = "Portrait"

    keywords = ['Portrait']
    flags = ["immediate", "no_block"]

class MultiRemovePortrait(EventCommand):
    nid = "multi_remove_portrait"
    nickname = "rr"
    tag = "Portrait"

    keywords = ['Portrait', 'Portrait']
    optional_keywords = ['Portrait', 'Portrait']

class MovePortrait(EventCommand):
    nid = "move_portrait"
    tag = "Portrait"

    keywords = ['Portrait', 'ScreenPosition']
    flags = ["immediate", "no_block"]

class BopPortrait(EventCommand):
    nid = "bop_portrait"
    nickname = "bop"
    tag = "Portrait"

    keywords = ['Portrait']
    flags = ["no_block"]

class Expression(EventCommand):
    nid = "expression"
    nickname = "e"
    tag = "Portrait"

    keywords = ['Portrait', 'ExpressionList']

class Speak(EventCommand):
    nid = "speak"
    nickname = "s"
    tag = "Dialogue/Text"

    keywords = ['Speaker', 'Text']
    optional_keywords = ['ScreenPosition', 'Width', 'DialogVariant']
    flags = ['low_priority']

class Transition(EventCommand):
    nid = "transition"
    nickname = "t"
    tag = "Background/Foreground"

    optional_keywords = ['Direction', 'Speed', 'Color3']

class Background(EventCommand):
    # Also does remove background
    nid = "change_background"
    nickname = "b"
    tag = "Background/Foreground"

    optional_keywords = ['Panorama']
    flags = ["keep_portraits"]

class DispCursor(EventCommand):
    nid = "disp_cursor"
    tag = "Cursor/Camera"

    keywords = ["Bool"]

class MoveCursor(EventCommand):
    nid = "move_cursor"
    nickname = "set_cursor"
    tag = "Cursor/Camera"
    
    keywords = ["Position"]
    flags = ["immediate"]

class CenterCursor(EventCommand):
    nid = "center_cursor"
    tag = "Cursor/Camera"
    
    keywords = ["Position"]
    flags = ["immediate"]

class FlickerCursor(EventCommand):
    nid = 'flicker_cursor'
    nickname = 'highlight'
    tag = "Cursor/Camera"

    keywords = ["Position"]
    flags = ["immediate"]

class GameVar(EventCommand):
    nid = 'game_var'
    tag = "Game-wide Unlocks and Variables"

    keywords = ["Nid", "Condition"]

class IncGameVar(EventCommand):
    nid = 'inc_game_var'
    tag = "Game-wide Unlocks and Variables"

    keywords = ["Nid"]
    optional_keywords = ["Condition"]

class LevelVar(EventCommand):
    nid = 'level_var'
    tag = "Level-wide Unlocks and Variables"

    keywords = ["Nid", "Condition"]

class IncLevelVar(EventCommand):
    nid = 'inc_level_var'
    tag = "Level-wide Unlocks and Variables"

    keywords = ["Nid"]
    optional_keywords = ["Condition"]

class WinGame(EventCommand):
    nid = 'win_game'
    tag = "Level-wide Unlocks and Variables"

class LoseGame(EventCommand):
    nid = 'lose_game'
    tag = "Level-wide Unlocks and Variables"

class ActivateTurnwheel(EventCommand):
    nid = 'activate_turnwheel'
    tag = "Miscellaneous"

    # Whether to force the player to move the turnwheel back
    # defaults to true
    optional_keywords = ['Bool']  

class BattleSave(EventCommand):
    nid = 'battle_save'
    tag = "Miscellaneous"

class ChangeTilemap(EventCommand):
    nid = 'change_tilemap'
    tag = "Tilemap"

    keywords = ["Tilemap"]
    flags = ["reload"]  # Should place units in previously recorded positions

class LoadUnit(EventCommand):
    nid = 'load_unit'
    tag = "Add/Remove/Interact with Units"

    keywords = ["UniqueUnit"]
    optional_keywords = ["Team", "AI"]

class MakeGeneric(EventCommand):
    nid = 'make_generic'
    tag = "Add/Remove/Interact with Units"

    # Nid, class, level, team, ai, faction, anim variant
    keywords = ["String", "Klass", "String", "Team"]
    optional_keywords = ["AI", "Faction", "String", "ItemList"]

class CreateUnit(EventCommand):
    nid = 'create_unit'
    tag = "Add/Remove/Interact with Units"
    # Unit template and new unit nid (can be '')
    keywords = ["Unit", "String"]
    # Unit level, position, entrytype, placement
    optional_keywords = ["String", "Position", "EntryType", "Placement"]

class AddUnit(EventCommand):
    nid = 'add_unit'
    nickname = 'add'
    tag = "Add/Remove/Interact with Units"

    keywords = ["Unit"]
    optional_keywords = ["Position", "EntryType", "Placement"]

class MoveUnit(EventCommand):
    nid = 'move_unit'
    nickname = 'move'
    tag = "Add/Remove/Interact with Units"

    keywords = ["Unit"]
    optional_keywords = ["Position", "MovementType", "Placement"]
    flags = ['no_block', 'no_follow']

class RemoveUnit(EventCommand):
    nid = 'remove_unit'
    nickname = 'remove'
    tag = "Add/Remove/Interact with Units"

    keywords = ["Unit"]
    optional_keywords = ["RemoveType"]

class KillUnit(EventCommand):
    nid = 'kill_unit'
    nickname = 'kill'
    tag = "Add/Remove/Interact with Units"

    keywords = ["Unit"]
    flags = ['immediate']

class RemoveAllUnits(EventCommand):
    nid = 'remove_all_units'
    tag = "Add/Remove/Interact with Units"

class RemoveAllEnemies(EventCommand):
    nid = 'remove_all_enemies'
    tag = "Add/Remove/Interact with Units"

class InteractUnit(EventCommand):
    nid = 'interact_unit'
    nickname = 'interact'
    tag = "Add/Remove/Interact with Units"

    keywords = ["Unit", "Unit"]
    optional_keywords = ["CombatScript", "Ability"]

class SetCurrentHP(EventCommand):
    nid = 'set_current_hp'
    tag = "Modify Unit Properties"
    keywords = ["Unit", "PositiveInteger"]

class Resurrect(EventCommand):
    nid = 'resurrect'
    tag = "Add/Remove/Interact with Units"
    keywords = ["GlobalUnit"]

class Reset(EventCommand):
    nid = 'reset'
    tag = "Modify Unit Properties"
    keywords = ["Unit"]

class HasAttacked(EventCommand):
    nid = 'has_attacked'
    tag = "Modify Unit Properties"
    keywords = ["Unit"]

class HasTraded(EventCommand):
    nid = 'has_traded'
    tag = "Modify Unit Properties"
    keywords = ['Unit']

class AddGroup(EventCommand):
    nid = 'add_group'
    tag = "Unit Groups"

    keywords = ["Group"]
    optional_keywords = ["StartingGroup", "EntryType", "Placement"]
    flags = ["create"]

class SpawnGroup(EventCommand):
    nid = 'spawn_group'
    tag = "Unit Groups"

    keywords = ["Group", "CardinalDirection", "StartingGroup"]
    optional_keywords = ["EntryType", "Placement"]
    flags = ["create", "no_block", 'no_follow']

class MoveGroup(EventCommand):
    nid = 'move_group'
    nickname = 'morph_group'
    tag = "Unit Groups"

    keywords = ["Group", "StartingGroup"]
    optional_keywords = ["MovementType", "Placement"]
    flags = ['no_block', 'no_follow']

class RemoveGroup(EventCommand):
    nid = 'remove_group'
    tag = "Unit Groups"

    keywords = ["Group"]
    optional_keywords = ["RemoveType"]

class GiveItem(EventCommand):
    nid = 'give_item'
    tag = "Modify Unit Properties"
    
    keywords = ["GlobalUnit", "Item"]
    flags = ['no_banner', 'no_choice', 'droppable']

class RemoveItem(EventCommand):
    nid = 'remove_item'
    tag = "Modify Unit Properties"
    
    keywords = ["GlobalUnit", "Item"]
    flags = ['no_banner']

class GiveMoney(EventCommand):
    nid = 'give_money'
    tag = 'Game-wide Unlocks and Variables'

    keywords = ["Integer"]
    optional_keywords = ["Party"]
    flags = ['no_banner']

class GiveExp(EventCommand):
    nid = 'give_exp'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "PositiveInteger"]

class SetExp(EventCommand):
    nid = 'set_exp'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "PositiveInteger"]

class GiveWexp(EventCommand):
    nid = 'give_wexp'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "WeaponType", "Integer"]
    flags = ['no_banner']

class GiveSkill(EventCommand):
    nid = 'give_skill'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "Skill"]
    flags = ['no_banner']

class RemoveSkill(EventCommand):
    nid = 'remove_skill'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "Skill"]
    flags = ['no_banner']

class ChangeAI(EventCommand):
    nid = 'change_ai'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "AI"] 

class ChangeTeam(EventCommand):
    nid = 'change_team'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit", "Team"]

class ChangePortrait(EventCommand):
    nid = 'change_portrait'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit", "PortraitNid"]

class ChangeStats(EventCommand):
    nid = 'change_stats'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit", "StatList"]
    flags = ['immediate']

class SetStats(EventCommand):
    nid = 'set_stats'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit", "StatList"]
    flags = ['immediate']

class AutolevelTo(EventCommand):
    nid = 'autolevel_to'
    tag = "Modify Unit Properties"
    # Second argument is level that is eval'd
    keywords = ["GlobalUnit", "String"]
    # Whether to actually change the unit's level
    flags = ["hidden"]

class Promote(EventCommand):
    nid = 'promote'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit"]
    optional_keywords = ["Klass"]

class ChangeClass(EventCommand):
    nid = 'change_class'
    tag = "Modify Unit Properties"
    keywords = ["GlobalUnit"]
    optional_keywords = ["Klass"]

class AddTag(EventCommand):
    nid = 'add_tag'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "Tag"]

class RemoveTag(EventCommand):
    nid = 'remove_tag'
    tag = "Modify Unit Properties"

    keywords = ["GlobalUnit", "Tag"]

class AddTalk(EventCommand):
    nid = 'add_talk'
    tag = 'Level-wide Unlocks and Variables'

    keywords = ["Unit", "Unit"]

class RemoveTalk(EventCommand):
    nid = 'remove_talk'
    tag = 'Level-wide Unlocks and Variables'

    keywords = ["Unit", "Unit"]

class AddLore(EventCommand):
    nid = 'add_lore'
    nickname = 'unlock_lore'
    tag = 'Game-wide Unlocks and Variables'

    keywords = ["Lore"]

class RemoveLore(EventCommand):
    nid = 'remove_lore'
    tag = 'Game-wide Unlocks and Variables'

    keywords = ["Lore"]

class AddBaseConvo(EventCommand):
    nid = 'add_base_convo'
    tag = 'Level-wide Unlocks and Variables'

    keywords = ["String"]

class IgnoreBaseConvo(EventCommand):
    nid = 'ignore_base_convo'
    tag = 'Level-wide Unlocks and Variables'

    keywords = ["String"]

class RemoveBaseConvo(EventCommand):
    nid = 'remove_base_convo'
    tag = 'Level-wide Unlocks and Variables'

    keywords = ["String"]

class IncrementSupportPoints(EventCommand):
    nid = 'increment_support_points'
    tag = "Modify Unit Properties"

    keywords = ['GlobalUnit', 'GlobalUnit', 'PositiveInteger']

class AddMarketItem(EventCommand):
    nid = 'add_market_item'
    tag = 'Game-wide Unlocks and Variables'

    keywords = ["Item"]

class RemoveMarketItem(EventCommand):
    nid = 'remove_market_item'
    tag = 'Game-wide Unlocks and Variables'

    keywords = ["Item"]

class AddRegion(EventCommand):
    nid = 'add_region'
    tag = "Region"

    keywords = ["Nid", "Position", "Size", "RegionType"]
    optional_keywords = ["String"]
    flags = ["only_once"]

class RegionCondition(EventCommand):
    nid = 'region_condition'
    tag = "Region"

    keywords = ["Nid", "Condition"]

class RemoveRegion(EventCommand):
    nid = 'remove_region'
    tag = "Region"

    keywords = ["Nid"]

class ShowLayer(EventCommand):
    nid = 'show_layer'
    tag = "Tilemap"

    keywords = ["Layer"]
    optional_keywords = ["LayerTransition"]

class HideLayer(EventCommand):
    nid = 'hide_layer'
    tag = "Tilemap"

    keywords = ["Layer"]
    optional_keywords = ["LayerTransition"]

class AddWeather(EventCommand):
    nid = 'add_weather'
    tag = "Tilemap"

    keywords = ["Weather"]

class RemoveWeather(EventCommand):
    nid = 'remove_weather'
    tag = "Tilemap"

    keywords = ["Weather"]

class ChangeObjectiveSimple(EventCommand):
    nid = 'change_objective_simple'
    tag = "Level-wide Unlocks and Variables"

    keywords = ["String"]

class ChangeObjectiveWin(EventCommand):
    nid = 'change_objective_win'
    tag = "Level-wide Unlocks and Variables"
    
    keywords = ["String"]

class ChangeObjectiveLoss(EventCommand):
    nid = 'change_objective_loss'
    tag = "Level-wide Unlocks and Variables"
    
    keywords = ["String"]

class SetPosition(EventCommand):
    nid = 'set_position'
    tag = "Miscellaneous"

    keywords = ["String"]

class MapAnim(EventCommand):
    nid = 'map_anim'
    tag = "Tilemap"

    keywords = ["MapAnim", "Position"]
    flags = ["no_block"]

class ArrangeFormation(EventCommand):
    nid = 'arrange_formation'
    tag = 'Miscellaneous'
    # Puts units on formation tiles automatically

class Prep(EventCommand):
    nid = 'prep'
    tag = 'Miscellaneous'

    optional_keywords = ["Bool", "Music"]  # Pick units

class Base(EventCommand):
    nid = 'base'
    tag = 'Miscellaneous'

    keywords = ["Panorama"]
    optional_keywords = ["Music"]

class Shop(EventCommand):
    nid = 'shop'
    tag = 'Miscellaneous'

    keywords = ["Unit", "ItemList"]
    optional_keywords = ["ShopFlavor"]

class Choice(EventCommand):
    nid = 'choice'
    tag = 'Miscellaneous'

    keywords = ['Nid', 'String', 'StringList']  
    optional_keywords = ['Orientation']

class ChapterTitle(EventCommand):
    nid = 'chapter_title'
    tag = 'Miscellaneous'

    optional_keywords = ["Music", "String"]

class Alert(EventCommand):
    nid = 'alert'
    tag = 'Dialogue/Text'

    keywords = ["String"]

class VictoryScreen(EventCommand):
    nid = 'victory_screen'
    tag = 'Miscellaneous'

class RecordsScreen(EventCommand):
    nid = 'records_screen'
    tag = 'Miscellaneous'

class LocationCard(EventCommand):
    nid = 'location_card'
    tag = "Dialogue/Text"

    keywords = ["String"]

class Credits(EventCommand):
    nid = 'credits'
    tag = "Dialogue/Text"

    keywords = ["String", "String"]
    flags = ['wait', 'center', 'no_split']

class Ending(EventCommand):
    nid = 'ending'
    tag = "Dialogue/Text"

    keywords = ["Portrait", "String", "String"]

class Unlock(EventCommand):
    nid = 'unlock'
    tag = "Region"

    keywords = ["Unit"]

class FindUnlock(EventCommand):
    nid = 'find_unlock'
    tag = 'Hidden'

    keywords = ["Unit"]

class SpendUnlock(EventCommand):
    nid = 'spend_unlock'
    tag = 'Hidden'

    keywords = ["Unit"]

class TriggerScript(EventCommand):
    nid = 'trigger_script'
    tag = "Miscellaneous"

    keywords = ["Event"]
    optional_keywords = ["GlobalUnit", "GlobalUnit"]
    
def get_commands():
    return EventCommand.__subclasses__()

def restore_command(dat):
    nid, values = dat
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == nid:
            copy = command(values)
            return copy
    print("Couldn't restore event command!")
    print(nid, values)
    return None

def parse_text(text):
    if text.startswith('#'):
        return Comment([text])
    arguments = text.split(';')
    command_nid = arguments[0]
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == command_nid or command.nickname == command_nid:
            copy = command(arguments[1:])
            return copy
    return None

def parse(command):
    values = command.values
    num_keywords = len(command.keywords)
    true_values = values[:num_keywords]
    flags = {v for v in values[num_keywords:] if v in command.flags}
    optional_keywords = [v for v in values[num_keywords:] if v not in flags]
    true_values += optional_keywords
    return true_values, flags
