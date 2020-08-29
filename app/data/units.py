from dataclasses import dataclass

from app.utilities.data import Data, Prefab
from app.data import stats, weapons
from app.data.skills import LearnedSkill

@dataclass
class UnitPrefab(Prefab):
    nid: str = None
    name: str = None
    desc: str = None
    variant: str = None

    level: int = None
    klass: str = None

    tags: list = None
    bases: stats.StatList = None
    growths: stats.StatList = None
    starting_items: list = None  # of tuples (ItemPrefab, droppable)

    learned_skills: list = None
    wexp_gain: weapons.WexpGainList = None

    alternate_classes: list = None

    portrait_nid: str = None

    def get_stat_titles(self):
        return ["Bases", "Growths"]

    def get_stat_lists(self):
        return [self.bases, self.growths]

    def get_items(self):
        return [i[0] for i in self.starting_items]

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def restore_attr(self, name, value):
        if name in ('bases', 'growths'):
            value = stats.StatList.restore(value)
        elif name == 'learned_skills':
            value = [LearnedSkill.restore(skill) for skill in value]
        elif name == 'wexp_gain':
            value = weapons.WexpGainList.restore(value)
        elif name == 'starting_items':
            # Need to convert to item nid + droppable
            value = [i if isinstance(i, list) else [i, False] for i in value]
        else:
            value = super().restore_attr(name, value)
        return value

class UnitCatalog(Data):
    datatype = UnitPrefab
