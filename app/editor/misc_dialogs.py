from app.data.database import DB

from app.editor.custom_gui import MultiAttrListDialog

class StatDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        return cls(DB.stats, "Stat", ("nid", "name", "maximum", "desc"), {"HP", "MOV"})

class RankDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        return cls(DB.weapon_ranks, "Weapon Rank", ("rank", "requirement", "accuracy", "damage", "crit"))

# Testing
# Run "python -m app.editor.misc_dialogs" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = StatDialog.create()
    window.show()
    app.exec_()