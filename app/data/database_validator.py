from app.data.weapons import WexpGain
from dataclasses import dataclass
import logging
from app.data.database import Database
from app.utilities.typing import NID
import re
from typing import List, Set

@dataclass
class ValidationError():
    category: str
    owner: str
    where: str
    what: str

    def __str__(self) -> str:
        return "Error in %s:%s:%s - %s" % self.category, self.owner, self.where, self.what

    @classmethod
    def does_not_exist(self, nid):
        return "%s does not exist" % nid

class DatabaseValidatorEngine():
    def __init__(self, db: Database):
        self.db = db

    def validate_unit(self, unit_nid):
        return unit_nid in self.db.units.keys()

    def validate_wtype(self, wtype_nid):
        return wtype_nid in self.db.weapons.keys()

    def validate_wrank(self, wrank_nid):
        return wrank_nid in self.db.weapons.keys()

    def validate_class(self, klass_nid):
        return klass_nid in self.db.classes.keys()

    def validate_tag(self, tag_nid):
        return tag_nid in self.db.tags.keys()

    def validate_item(self, item_nid):
        return item_nid in self.db.items.keys()

    def validate_skill(self, skill_nid):
        return skill_nid in self.db.skills.keys()

    def validate_stat(self, stat_nid):
        return stat_nid in self.db.stats.keys()

    def validate_units(self):
        errors: List[ValidationError] = []
        for unit in self.db.units:
            if not self.validate_class(unit.klass):
                errors.append(ValidationError("Units", unit.nid, "klass", ValidationError.does_not_exist(unit.klass)))
        return errors

    def validate(self):
        # @TODO(mag): WIP
        errors: List[ValidationError] = []
        errors += self.validate_units()
        for error in errors:
            logging.error("validation failed: %s", error)
        return errors

    def repair_units(self):
        all_weapon_types = set(self.db.weapons.keys())
        all_stats = set(self.db.stats.keys())
        for unit in self.db.units:
            # make sure each unit has an entry for every weapon type, and no extraneous ones
            uweapons = set(unit.wexp_gain.keys())
            missing_weapon_types = all_weapon_types - uweapons
            extraneous_weapon_types = uweapons - all_weapon_types
            for wtype in missing_weapon_types:
                unit.wexp_gain[wtype] = WexpGain(False, 0)
            for wtype in extraneous_weapon_types:
                del unit.wexp_gain[wtype]
            # make sure each unit has an entry for every stat, and no extraneous ones
            ubstats = set(unit.bases.keys())
            missing_stats = all_stats - ubstats
            extraneous_stats = ubstats - all_stats
            for stype in missing_stats:
                unit.bases[stype] = 0
            for stype in extraneous_stats:
                del unit.bases[stype]
            ugstats = set(unit.growths.keys())
            missing_stats = all_stats - ugstats
            extraneous_stats = ugstats - all_stats
            for stype in missing_stats:
                unit.growths[stype] = 0
            for stype in extraneous_stats:
                del unit.growths[stype]

    def repair(self):
        """Only obvious repairs should be done here.
        """
        self.repair_units()