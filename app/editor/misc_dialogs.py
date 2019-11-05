from app.data.database import DB

from app.editor.custom_gui import MultiAttrListDialog

class TagDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        return cls(DB.tags, "Tag", ("nid"))

class StatDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        return cls(DB.stats, "Stat", ("nid", "name", "maximum", "desc"), 
                   {"HP", "MOV"})

class RankDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        return cls(DB.weapon_ranks, "Weapon Rank", 
                   ("rank", "requirement", "accuracy", "damage", "crit"))

class EquationDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        dlg = cls(DB.equations, "Equation", ("nid", "expression"), 
                  {"ATTACKSPEED", "HIT", "AVOID", "CRIT_HIT", "CRIT_AVOID", 
                   "DAMAGE", "DEFENSE", "MAGIC_DAMAGE", "MAGIC_DEFENSE", 
                   "CRIT_ADD", "CRIT_MULT",
                   "DOUBLE_ATK", "DOUBLE_DEF", "STEAL_ATK", "STEAL_DEF", 
                   "HEAL", "RESCUE_AID", "RESCUE_WEIGHT", "RATING"})
        return dlg

# Testing
# Run "python -m app.editor.misc_dialogs" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = StatDialog.create()
    window.show()
    app.exec_()
