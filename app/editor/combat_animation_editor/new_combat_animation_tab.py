from typing import Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget

from app.data.resources.resources import RESOURCES
from app.data.resources.combat_anims import CombatCatalog, CombatEffectCatalog

from app.editor.new_editor_tab import NewEditorTab
from app.editor.combat_animation_editor import combat_animation_model
from app.editor.combat_animation_editor.new_combat_animation_properties import CombatAnimProperties
from app.editor.combat_animation_editor.new_combat_effect_properties import CombatEffectProperties
from app.editor.combat_animation_editor.new_palette_tab import NewPaletteTab
from app.editor.data_editor import SingleResourceEditor, MultiResourceEditor
from app.utilities.typing import NID

class SimpleCombatAnimProperties(QWidget):
    title = "Combat Animation"

    def __init__(self, parent, current=None):
        QWidget.__init__(self, parent)
        self.window = parent
        self.current = current

    def set_current(self, current):
        self.current = current

class CombatAnimDisplay(NewEditorTab):
    catalog_type = CombatCatalog
    properties_type = CombatAnimProperties

    @classmethod
    def edit(cls, parent=None):
        window = SingleResourceEditor(CombatAnimDisplay, ['combat_anims'], parent)
        window.exec_()

    @property
    def data(self):
        return self._res.combat_anims

    def get_icon(self, combat_anim_nid: NID) -> Optional[QIcon]:
        if not self.data.get(combat_anim_nid):
            return None
        pix = combat_animation_model.get_combat_anim_icon(combat_anim_nid)
        if pix:
            return QIcon(pix)
        return None

class SimpleCombatAnimDisplay(CombatAnimDisplay):
    properties_type = SimpleCombatAnimProperties

    @classmethod
    def edit(cls, parent=None):
        window = SingleResourceEditor(SimpleCombatAnimDisplay, ['combat_anims'], parent)
        window.exec_()

class CombatEffectDisplay(NewEditorTab):
    catalog_type = CombatEffectCatalog
    properties_type = CombatEffectProperties

    @classmethod
    def edit(cls, parent=None):
        window = SingleResourceEditor(CombatEffectDisplay, ['combat_effects'], parent)
        window.exec_()

    @property
    def data(self):
        return self._res.combat_effects

    def get_icon(self, combat_anim_nid: NID) -> Optional[QIcon]:
        if not self.data.get(combat_anim_nid):
            return None
        pix = combat_animation_model.get_combat_anim_icon(combat_anim_nid)
        if pix:
            return pix
        return None

def get_full_editor() -> MultiResourceEditor:
    editor = MultiResourceEditor((CombatAnimDisplay, CombatEffectDisplay, NewPaletteTab),
                                 ('combat_anims', 'combat_effects', 'combat_palettes'))
    editor.setWindowTitle("Combat Animation Editor")
    return editor

def get_animations() -> tuple:
    window = SingleResourceEditor(SimpleCombatAnimDisplay, ['combat_anims'])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_combat_anim = window.tab.right_frame.current
        return selected_combat_anim, True
    else:
        return None, False
