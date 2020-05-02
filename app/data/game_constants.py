from app.data.data import Data

class Constant(object):
    def __init__(self, nid=None, name='', attr=bool, value=False):
        self.nid = nid
        self.name = name
        self.attr = attr
        self.value = value

    def set_value(self, val):
        self.value = val

    def __getstate__(self):
        return self.nid, self.value

    def __setstate__(self, state):
        self.nid, self.value = state

    def serialize(self):
        return (self.nid, self.value)

class ConstantCatalog(Data):
    datatype = Constant

    def save(self):
        return [l.serialize() for l in self._list]

    def restore(self, vals):
        for dat in vals:
            nid, value = dat
            base = self.get(nid)
            if base:
                base.value = value

    def max_items(self):
        return self.get('num_items').value + self.get('num_accessories').value

constants = ConstantCatalog([
    Constant('num_items', "Max number of Items in inventory", int, 5),
    Constant('num_accessories', "Max number of Accessories in inventory", int, 0),
    Constant('turnwheel', "Turnwheel", bool),
    Constant('overworld', "Overworld", bool),
    Constant('crit', "Allow Criticals", bool, True),
    Constant('permadeath', "Permadeath", bool, True),
    Constant('line_of_sight', "Force weapons to obey line of sight rules", bool),
    Constant('spell_los', "Force spells to obey line of sight rules", bool),
    Constant('aura_los', "Force auras to obey line of sight rules", bool),
    Constant('def_double', "Defender can double counterattack", bool, True),
    Constant('player_leveling', 'Method for leveling player units', ("Random", "Fixed", "Dynamic"), "Random"),
    Constant('enemy_leveling', "Method for autoleveling generic units", ("Random", "Fixed", "Dynamic", "Match"), "Match"),
    Constant('rng', "Method for resolving accuracy rolls", ("Classic", "True Hit", "True Hit+", "Grandmaster"), "True Hit"),
    # Constant('num_skills', "Expected number of Skills at max level", int, 5),
    Constant('auto_promote', "Units will promote automatically upon reaching max level", bool),
    Constant('min_damage', "Min damage dealt by an attack", int, 0),
    Constant('boss_crit', "Final blow on boss will use critical animation", bool),
    Constant('convoy_on_death', "Weapons held by dead units are sent to convoy", bool),
    Constant('steal', "Steal Type", ("Nonweapons", "All unequipped"), "Nonweapons"),
    Constant('num_save_slots', "Number of save slots", int, 3),
    Constant('attack_zero_hit', "Enemy AI attacks even if Hit is 0", bool, True),
    Constant('attack_zero_dam', "Enemy AI attacks even if Damage is 0", bool, True),
    Constant('zero_move', "Treat Movement as 0 if AI does not move", bool, False),
    Constant('title', "Game Title", str, "Lex Talionis Game"),
    Constant('kill_wexp', "Double weapon exp gained on kill", bool, True),
    Constant('double_wexp', "Each hit when doubling grants weapon exp", bool, True),
    Constant('miss_wexp', "Gain weapon exp even on miss", bool, True),
    # Experience constants below
    Constant('exp_curve', "How linear the exp curve is; Higher = less linear", 'ufloat', 0.035),
    Constant('exp_magnitude', "How much base exp is received for each interaction", 'ufloat', 10),
    Constant('exp_offset', "Tries to keep player character this many levels above enemies", float, 0),
    Constant('kill_multiplier', "Exp multiplier on kill", 'ufloat', 3),
    Constant('boss_bonus', "Extra exp for killing a boss", int, 40),
    Constant('min_exp', "Min exp gained in combat", int, 1),
    Constant('default_exp', "Default exp gain", 'ufloat', 11),
    Constant('steal_exp', "Exp gained on steal", 'ufloat', 0),
    Constant('heal_curve', "How much to multiply the amount healed by to determine experience gain", 'ufloat', 0),
    Constant('heal_magnitude', "Added to total exp for healing", 'int', 0),
    Constant('heal_offset', "Modifies expected healing", 'float', 11),
    Constant('heal_min', "Min exp gained for healing", 'float', 11)])
