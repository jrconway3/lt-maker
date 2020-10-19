from app.utilities.data import Data

class Constant(object):
    def __init__(self, nid=None, name='', attr=bool, value=False, tag='other'):
        self.nid = nid
        self.name = name
        self.attr = attr
        self.value = value
        self.tag = tag

    def set_value(self, val):
        self.value = val

    def save(self):
        return (self.nid, self.value)

class ConstantCatalog(Data):
    def save(self):
        return [elem.save() for elem in self._list]

    def restore(self, ser_data):
        # Assign each constant with the correct value
        for nid, value in ser_data:
            constant = self.get(nid)
            if constant:
                constant.value = value

    def value(self, val):
        return self.get(val).value

tags = ['title', 'features', 'inventory', 'line_of_sight', 'leveling', 'ai', 'wexp', 'other']

constants = ConstantCatalog([
    Constant('num_items', "Max number of Items in inventory", int, 5, 'inventory'),
    Constant('num_accessories', "Max number of Accessories in inventory", int, 0, 'inventory'),
    Constant('turnwheel', "Turnwheel", bool, False, 'features'),
    Constant('fatigue', "Fatigue", bool, False, 'features'),
    Constant('support', "Supports", bool, False, 'features'),
    Constant('overworld', "Overworld", bool, False, 'features'),
    Constant('crit', "Allow Criticals", bool, True, 'features'),
    Constant('permadeath', "Permadeath", bool, True, 'features'),
    Constant('trade', "Can trade items on map", bool, True, 'features'),
    Constant('line_of_sight', "Force weapons to obey line of sight rules", bool, 'line_of_sight'),
    Constant('spell_los', "Force spells to obey line of sight rules", bool, 'line_of_sight'),
    Constant('aura_los', "Force auras to obey line of sight rules", bool, 'line_of_sight'),
    Constant('def_double', "Defender can double counterattack", bool, True, 'features'),
    Constant('player_leveling', 'Method for leveling player units', ("Random", "Fixed", "Dynamic"), "Random", 'leveling'),
    Constant('enemy_leveling', "Method for autoleveling generic units", ("Random", "Fixed", "Dynamic", "Match"), "Match", 'leveling'),
    Constant('rng', "Method for resolving accuracy rolls", ("Classic", "True Hit", "True Hit+", "Grandmaster"), "True Hit", 'leveling'),
    Constant('auto_promote', "Units will promote automatically upon reaching max level", bool, 'leveling'),
    Constant('min_damage', "Min damage dealt by an attack", int, 0),
    Constant('boss_crit', "Final blow on boss will use critical animation", bool),
    Constant('convoy_on_death', "Weapons held by dead player units are sent to convoy", bool),
    # Constant('steal', "Steal Type", ("Nonweapons", "All unequipped"), "Nonweapons"),
    Constant('num_save_slots', "Number of save slots", int, 3, 'title'),
    Constant('attack_zero_hit', "Enemy AI attacks even if Hit is 0", bool, True, 'ai'),
    Constant('attack_zero_dam', "Enemy AI attacks even if Damage is 0", bool, True, 'ai'),
    Constant('zero_move', "Show Movement as 0 if AI does not move", bool, False, 'ai'),
    Constant('game_nid', "Game Unique Identifier", str, "LT", 'title'),
    Constant('title', "Game Title", str, "Lex Talionis Game", 'title'),
    Constant('kill_wexp', "Kills give double weapon exp", bool, True, 'wexp'),
    Constant('double_wexp', "Each hit when doubling grants weapon exp", bool, True, 'wexp'),
    Constant('miss_wexp', "Gain weapon exp even on miss", bool, True, 'wexp'),
    # Experience constants below
    Constant('exp_curve', "How linear the exp curve is; Higher = less linear", float, 0.035, 'exp'),
    Constant('exp_magnitude', "How much base exp is received for each interaction", float, 10, 'exp'),
    Constant('exp_offset', "Tries to keep player character this many levels above enemies", int, 0, 'exp'),
    Constant('kill_multiplier', "Exp multiplier on kill", float, 3, 'exp'),
    Constant('boss_bonus', "Extra exp for killing a boss", int, 40, 'exp'),
    Constant('min_exp', "Min exp gained in combat", int, 1, 'exp'),
    Constant('default_exp', "Default exp gain", int, 11, 'exp'),
    Constant('steal_exp', "Exp gained on steal", int, 0, 'exp'),
    Constant('heal_curve', "How much to multiply the amount healed by to determine experience gain", float, 0, 'exp'),
    Constant('heal_magnitude', "Added to total exp for healing", int, 0, 'exp'),
    Constant('heal_offset', "Modifies expected healing", int, 11, 'exp'),
    Constant('heal_min', "Min exp gained for healing", int, 11, 'exp')])
