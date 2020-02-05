class LearnedSkill(object):
    def __init__(self, level, skill_nid):
        self.level = level
        self.skill_nid = skill_nid

    def serialize(self):
        return (self.level, self.skill_nid)

    @classmethod
    def deserialize(cls, s_tuple):
        return cls(*s_tuple)

class LearnedSkillList(list):
    def add_new_default(self, db):
        new_class_skill = LearnedSkill(1, "None")
        self.append(new_class_skill)
