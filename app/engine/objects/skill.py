from app.utilities.data import Data

from app.data.database import DB

class SkillObject():
    next_uid = 100

    def __init__(self, nid, name, desc, icon_nid=None, icon_index=(0, 0), components=None):
        self.uid = SkillObject.next_uid
        SkillObject.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc

        self.icon_nid = icon_nid
        self.icon_index = icon_index

        self.components = components or Data()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value
            # Assign parent to component
            component_value.skill = self

        self.data = {}

    @classmethod
    def from_prefab(cls, prefab):
        return cls(prefab.nid, prefab.name, prefab.desc, prefab.icon_nid, prefab.icon_index, prefab.components)

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Skill: %s %s" % (self.nid, self.uid)

    def save(self):
        serial_dict = {}
        serial_dict['uid'] = self.uid
        serial_dict['nid'] = self.nid
        serial_dict['owner_nid'] = self.owner_nid
        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def restore(cls, dat):
        self = cls.from_prefab(DB.skills.get(dat['nid']))
        self.uid = dat['uid']
        self.owner_nid = dat['owner_nid']
        self.data = dat['data']
        return self
