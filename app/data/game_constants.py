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
            base.value = value

constants = ConstantCatalog([
    Constant('num_items', "Maximum number of Items in inventory", int, 5),
    Constant('num_accessories', "Maximum number of Accessories in inventory", int, 0),
    Constant('turnwheel', "Turnwheel", bool),
    Constant('overworld', "Overworld", bool),
    Constant('line_of_sight', "Force weapons to obey line of sight rules", bool),
    Constant('spell_los', "Force spells to obey line of sight rules", bool),
    Constant('aura_los', "Force auras to obey line of sight rules", bool),
    Constant('def_double', "Defender can double counterattack", bool, True),
    Constant('enemy_leveling', "Method for autoleveling generic units", ("Random", "Fixed", "Hybrid", "FE8", "Match"), "Match"),
    Constant('rng', "Method for resolving accuracy rolls", ("Classic", "True Hit", "True Hit+", "Grandmaster"), "True Hit"),
    Constant('num_skills', "Expected number of Skills at max level", int, 5),
    Constant('auto_promote', "Units will promote automatically upon reaching maximum level", bool),
    Constant('min_damage', "Minimum damage dealt by an attack", int, 0),
    Constant('boss_crit', "Final blow on boss will use critical animation", bool),
    Constant('unarmed_disadvantage', "Amount of weapon disadvantage suffered by unarmed units", int, 0),
    Constant('convoy_on_death', "Weapons held by dead units are sent to convoy", bool),
    Constant('steal', "Steal Type", ("Nonweapons", "All unequipped"), "Nonweapons"),
    Constant('num_save_slots', "Number of save slots", int, 3),
    Constant('attack_zero_hit', "Enemy AI attacks even if Hit is 0", bool, True),
    Constant('attack_zero_dam', "Enemy AI attacks even if Damage is 0", bool, True),
    Constant('zero_move', "Treat Movement as 0 if AI does not move", bool, False),
    Constant('title', "Game Title", str, "Lex Talionis Game"),
    Constant('kill_wexp', "Double weapon experience gained on kill", bool, True),
    Constant('double_wexp', "Each hit when doubling grants weapon experience", bool, True),
    Constant('miss_wexp', "Gain weapon experience even on miss", bool, True)])
