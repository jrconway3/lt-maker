from app.utilities.data import Prefab

class DifficultyModeObject(Prefab):
    def __init__(self, nid, permadeath=False, growths='Fixed'):
        self.nid: str = nid
        self.permadeath: bool = permadeath
        self.growths: str = growths

    def save(self):
        return {'nid': self.nid, 
                'permadeath': self.permadeath, 
                'growths': self.growths,
                }

    @classmethod
    def restore(cls, s_dict):
        difficulty_mode = cls(s_dict['nid'], s_dict['permadeath'], s_dict['growths'])
        return difficulty_mode
