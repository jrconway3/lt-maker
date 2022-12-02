from __future__ import annotations

from typing import Optional

from PyQt5.QtGui import QIcon

import app.engine.skill_component_access as SCA
from app.data.database.skills import SkillCatalog, SkillPrefab
from app.editor import timer
from app.editor.component_object_editor import ComponentObjectEditor
from app.editor.data_editor import SingleDatabaseEditor
from app.editor.item_skill_properties import NewComponentProperties
from app.editor.skill_editor import skill_model


class NewSkillProperties(NewComponentProperties[SkillPrefab]):
    title = "Skill"
    get_components = staticmethod(SCA.get_skill_components)
    get_templates = staticmethod(SCA.get_templates)
    get_tags = staticmethod(SCA.get_skill_tags)


class NewSkillDatabase(ComponentObjectEditor):
    catalog_type = SkillCatalog

    @classmethod
    def edit(cls, parent=None):
        timer.get_timer().stop_for_editor()  # Don't need these while running game
        window = SingleDatabaseEditor(NewSkillDatabase, parent)
        window.exec_()
        timer.get_timer().start_for_editor()

    @property
    def data(self):
        return self._db.skills

    def get_icon(self, skill_nid) -> Optional[QIcon]:
        pix = skill_model.get_pixmap(self.data.get(skill_nid))
        if pix:
            return QIcon(pix.scaled(32, 32))
        return None

    def import_csv(self):
        return
