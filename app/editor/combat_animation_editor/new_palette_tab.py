from PyQt5.QtWidgets import QDialog

from app.data.resources.resources import RESOURCES
from app.data.resources.combat_palettes import PaletteCatalog

from app.editor.data_editor import SingleResourceEditor
from app.editor.new_editor_tab import NewEditorTab

from app.editor.combat_animation_editor import new_palette_properties, palette_model

class NewPaletteTab(NewEditorTab):
    catalog_type = PaletteCatalog
    properties_type = new_palette_properties.NewPaletteProperties

    @property
    def data(self):
        return self._res.combat_palettes

    @classmethod
    def edit(cls, parent=None):
        window = SingleResourceEditor(NewPaletteTab, ['combat_palettes'], parent)
        window.exec_()

def get():
    window = SingleResourceEditor(NewPaletteTab, ['combat_palettes'])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_palette = window.tab.right_frame.current
        return selected_palette, True
    else:
        return None, False

# Testing
# Run "python -m app.editor.combat_animation_editor.palette_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from app.editor.combat_animation_editor.new_combat_animation_properties import populate_anim_pixmaps
    app = QApplication(sys.argv)
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    RESOURCES.load('sacred_stones.ltproj', CURRENT_SERIALIZATION_VERSION)
    for anim in RESOURCES.combat_anims:
        populate_anim_pixmaps(anim)
    window = SingleResourceEditor(NewPaletteTab, ['combat_palettes'])
    window.show()
    app.exec_()
