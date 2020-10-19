import os
import shutil

from app.resources.base_catalog import ManifestCatalog

class Song():
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path

        # Mutually exclusive. Can't have both start and battle versions
        self.intro_full_path = None
        self.battle_full_path = None

    def set_full_path(self, full_path):
        self.full_path = full_path

    def set_intro_full_path(self, full_path):
        self.intro_full_path = full_path

    def set_battle_full_path(self, full_path):
        self.battle_full_path = full_path

    def save(self):
        return (self.nid, True if self.intro_full_path else False, True if self.battle_full_path else False)

    @classmethod
    def restore(cls, s_tuple):
        self = cls(s_tuple[0])
        self.intro_full_path = s_tuple[1]
        self.battle_full_path = s_tuple[2]
        return self

class MusicCatalog(ManifestCatalog):
    manifest = 'music.json'
    title = 'music'
    filetype = '.ogg'

    def load(self, loc):
        music_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in music_dict:
            new_song = Song.restore(s_dict)
            new_song.set_full_path(os.path.join(loc, new_song.nid + '.ogg'))
            if new_song.battle_full_path:
                new_song.set_battle_full_path(os.path.join(loc, new_song.nid + '-battle.ogg'))
            if new_song.intro_full_path:
                new_song.set_intro_full_path(os.path.join(loc, new_song.nid + '-intro.ogg'))
            self.append(new_song)

    def save(self, loc):
        for song in self:
            # Full Path
            new_full_path = os.path.join(loc, song.nid + '.ogg')
            if os.path.abspath(song.full_path) != os.path.abspath(new_full_path):
                shutil.copy(song.full_path, new_full_path)
                song.set_full_path(new_full_path)
            # Battle Full Path
            new_full_path = os.path.join(loc, song.nid + '-battle.ogg')
            if song.battle_full_path and os.path.abspath(song.battle_full_path) != os.path.abspath(new_full_path):
                shutil.copy(song.battle_full_path, new_full_path)
                song.set_battle_full_path(new_full_path)
            # Intro Full Path
            new_full_path = os.path.join(loc, song.nid + '-intro.ogg')
            if song.intro_full_path and os.path.abspath(song.intro_full_path) != os.path.abspath(new_full_path):
                shutil.copy(song.intro_full_path, new_full_path)
                song.set_intro_full_path(new_full_path)
        self.dump(loc)

class SFX():
    def __init__(self, nid, full_path=None, tag=None):
        self.nid = nid
        self.tag = None
        self.full_path = full_path

    def set_full_path(self, full_path):
        self.full_path = full_path

    def save(self):
        return (self.nid, self.tag)

    @classmethod
    def restore(cls, s_tuple):
        self = cls(s_tuple[0], tag=s_tuple[1])
        return self

class SFXCatalog(ManifestCatalog):
    manifest = 'sfx.json'
    title = 'sfx'
    filetype = '.ogg'

    def load(self, loc):
        sfx_dict = self.read_manifest(os.path.join(loc, self.manifest))
        temp_list = []
        for s_tuple in sfx_dict:
            new_sfx = SFX.restore(s_tuple)
            new_sfx.set_full_path(os.path.join(loc, new_sfx.nid + self.filetype))
            temp_list.append(new_sfx)
        # Need to sort according to tag
        temp_list = sorted(temp_list, key=lambda x: x.tag if x.tag else '____')
        for sfx in temp_list:
            self.append(sfx)
