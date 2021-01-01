from app.utilities.data import Data
from app.data.skill_components import SkillComponent, tags

def get_skill_components():
    from app.engine import skill_components

    subclasses = SkillComponent.__subclasses__()
    # Sort by tag
    subclasses = sorted(subclasses, key=lambda x: tags.index(x.tag) if x.tag in tags else 100)
    return Data(subclasses)

def get_component(nid):
    _skill_components = get_skill_components()
    base_class = _skill_components.get(nid)
    if base_class:
        return base_class(base_class.value)
    return None

def restore_component(dat):
    nid, value = dat
    _skill_components = get_skill_components()
    base_class = _skill_components.get(nid)
    if base_class:
        copy = base_class(value)
        return copy
    return None

templates = {}

def get_templates():
    return templates.items()
