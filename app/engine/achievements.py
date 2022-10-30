
try:
    import cPickle as pickle
except ImportError:
    import pickle

import logging

class Achievement():
    def __init__(self, nid: str, name:str, desc: str, complete: bool, hidden=False):
        self.nid = nid
        self.name = name
        self.desc = desc
        self.complete = complete
        self.hidden = hidden

    def set_complete(self, complete: bool):
        self.complete = complete

    def get_complete(self) -> bool:
        return bool(self.complete)

    def get_hidden(self) -> bool:
        return bool(self.hidden)

    def save(self):
        ser_dict = {}
        for attr in self.__dict__.items():
            name, value = attr
            ser_dict[name] = value
        return (self.__class__.__name__, ser_dict)

    @classmethod
    def restore(cls, ser_dict):
        self = cls.__new__(cls)
        for name, value in ser_dict.items():
            setattr(self, name, value)
        return self

class AchievementManager():
    def __init__(self, game_id) -> None:
        self.achievements = [] # A list of Achievement() classes
        self.location = 'saves/' + game_id + '-achievements.p'
        self.load_achievements()

    def __contains__(self, achievement) -> None:
        return achievement in self.achievements

    def __iter__(self):
        return iter(self.achievements)

    def __len__(self):
        return len(self.achievements)

    def get_data(self) -> list:
        save_data = []
        for a in self.achievements:
            save_data.append(a.save())
        return save_data

    def achievement_defined(self, nid: str):
        for a in self.achievements:
            if a.nid == nid:
                return True
        return False

    def get_achievement(self, nid: str):
        for a in self.achievements:
            if a.nid == nid:
                return a
        return None

    def add_achievement(self, nid: str, name:str, desc: str, complete=False, hidden=False):
        if not self.achievement_defined(nid):
            self.achievements.append(Achievement(nid, name, desc, complete, hidden))
        else:
            logging.info("Attempted to define already existing achievement with nid %s", nid)
        self.save_achievements()

    def update_achievement(self, nid, name, desc, hidden):
        a = self.get_achievement(nid)
        if a:
            a.name = name
            a.desc = desc
            a.hidden = hidden
        else:
            logging.info("Attempted to update non-existant achievement with nid %s", nid)
        self.save_achievements()

    def remove_achievement(self, nid: str):
        for a in self.achievements:
            if a.nid == nid:
                self.achievements.remove(a)
                self.save_achievements()
                return
        logging.info("Attempted to remove non-existant achievement with nid %s", nid)

    def check_achievement(self, nid: str) -> bool:
        for a in self.achievements:
            if a.nid == nid and a.get_complete():
                return True
        return False

    def complete_achievement(self, nid: str, complete: bool):
        for a in self.achievements:
            if a.nid == nid:
                a.set_complete(complete)
                self.save_achievements()
                return
        logging.info("Attempted to complete non-existant achievement with nid %s", nid)

    def save_achievements(self):
        logging.info("Saving achievements to %s", self.location)
        data = self.get_data()
        with open(self.location, 'wb') as fp:
            try:
                pickle.dump(data, fp)
            except TypeError as e:
                # There's a surface somewhere in the dictionary of things to save...
                print(data)
                print(e)

    def load_achievements(self):
        logging.info("Loading achievements from %s", self.location)
        try:
            with open(self.location, 'rb') as fp:
                s_dict = pickle.load(fp)
            if s_dict:
                for data in s_dict:
                    self.achievements.append(Achievement.restore(data[1]))
        except FileNotFoundError:
            logging.info("No achievements file found")

    def clear_achievements(self):
        logging.info("Clearing achievements in %s", self.location)
        self.achievements = []
        with open(self.location, 'wb') as fp:
            pickle.dump(self.achievements, fp)