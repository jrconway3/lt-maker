from app.utilities import str_utils

class SkillComponent():
    nid: str = None
    desc: str = None
    author: str = 'rainlash'

    @property
    def name(self):
        name = self.__class__.__name__
        return str_utils.camel_case(name)

    def defines(self, function_name):
        return hasattr(self, function_name)
