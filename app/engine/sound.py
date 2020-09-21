import pygame

from app.utilities import utils
from app.resources.resources import RESOURCES
from app.engine import engine

import logging
logger = logging.getLogger(__name__)

class Song():
    def __init__(self, prefab):
        self.nid = prefab.nid
        self.song = pygame.mixer.Sound(prefab.full_path)
        self.battle = pygame.mixer.Sound(prefab.battle_full_path) if prefab.battle_full_path else None
        self.intro = pygame.mixer.Sound(prefab.intro_full_path) if prefab.intro_full_path else None

        self.channel = None

    def battle(self):
        return self.battle

class MusicDict(dict):
    def get(self, val):
        if val not in self:
            prefab = RESOURCES.music.get(val)
            if prefab:
                self[val] = Song(prefab)
            else:
                return None
        return self[val]

MUSIC = MusicDict()

class SoundDict(dict):
    def get(self, val):
        if val not in self:
            sfx = RESOURCES.sfx.get(val)
            if sfx:
                self[val] = pygame.mixer.Sound(sfx.full_path)
            else:
                return None
        return self[val]

SFX = SoundDict()

class Channel():
    fade_in_time = 400
    fade_out_time = 400
    playing_states = ("playing", "fade_out", "crossfade_out", "fade_in", "crossfade_in")

    def __init__(self, name, nid, end_event):
        self.name = name
        self.nid: int = nid
        self._channel = pygame.mixer.Channel(nid)
        self.local_volume = 0
        self.global_volume = 0

        self.end_event = end_event
        self._channel.set_endevent(end_event)

        self.current_song = None
        self.played_intro = False
        self.num_plays = -1

        self.last_state = "stopped"  # stopped, paused, playing
        self.state = "stopped"  # stopped, paused, fade_out, fade_in, playing
        self.last_update = 0

    def update(self, event_list, current_time):
        if self.state == "stopped":
            pass
        if self.state in self.playing_states:
            for event in event_list:
                if event.type == self._channel.get_endevent():
                    self._play()
        if self.state == "paused":
            pass
        if self.state in ("fade_out", "crossfade_out"):
            progress = utils.clamp((current_time - self.last_update) / self.fade_out_time, 0, 1)
            self.local_volume = 1 - progress
            self._channel.set_volume(self.local_volume * self.global_volume)
            if progress >= 1:
                if self.state == 'fade_out':
                    self.state = "paused"
                    self._channel.pause()
                    return True
                elif self.state == 'crossfade_out':
                    self.state = "playing"
        if self.state in ("fade_in", "crossfade_in"):
            progress = utils.clamp((current_time - self.last_update) / self.fade_in_time, 0, 1)
            self.local_volume = progress
            self._channel.set_volume(self.local_volume * self.global_volume)
            if progress >= 1:
                self.state = "playing"
                return True
        return False

    def _play(self):
        if self.num_plays == 0:
            self.last_state = "stopped"
            self.state = "stopped"
            return
        if self.num_plays > 0:
            self.num_plays -= 1

        if self.name == "battle":
            if self.current_song.battle:
                self._channel.play(self.current_song.battle, 0)
        else:
            if self.current_song.intro and not self.played_intro:
                self._channel.play(self.current_song.intro, 0)
                self.played_intro = True
            else:
                self._channel.play(self.current_song.song, 0)

    def set_current_song(self, song, num_plays=-1):
        self.current_song = song
        self.num_plays = num_plays
        self.played_intro = False

    def clear(self):
        self.current_song = None
        self.num_plays = 0
        self.played_intro = False
        self.last_state = "stopped"
        self.state = "stopped"

    def fade_in(self):
        if self.last_state == "paused":
            self._channel.unpause()
        elif self.last_state == "stopped":
            self._play()
        self.last_state = self.state
        self.state = "fade_in"
        self.last_update = engine.get_time()

    def fade_out(self):
        self.last_state = self.state
        self.state = "fade_out"
        self.last_update = engine.get_time()

    def crossfade_in(self):
        self.last_state = "playing"
        self.state = "crossfade_in"
        self.last_update = engine.get_time()

    def crossfade_out(self):
        self.last_state = "playing"
        self.state = "crossfade_out"
        self.last_update = engine.get_time()

    def pause(self):
        self._channel.pause()
        self.last_state = "paused"
        self.state = "paused"

    def resume(self):
        self._channel.unpause()
        self.last_state = "playing"
        self.state = "playing"

    def stop(self):
        self._channel.stop()
        self.last_state = "stopped"
        self.state = "stopped"

    def set_volume(self, volume):
        self.global_volume = volume
        self._channel.set_volume(self.local_volume * self.global_volume)

class ChannelPair():
    def __init__(self, nid):
        event = pygame.USEREVENT + nid//2  # 24, 25, 26, 27

        self.channel = Channel("music", nid, event)
        self.battle = Channel("battle", nid + 1, event)

        self.battle_mode = False
        self.battle.local_volume = 0

        self.current_song = None

    def is_playing(self):
        return (self.channel.state in self.channel.playing_states) or \
            (self.battle.state in self.battle.playing_states)

    def update(self, event_list, current_time):
        res1 = self.channel.update(event_list, current_time)
        res2 = self.battle.update(event_list, current_time)
        return res1 or res2

    def set_current_song(self, song, num_plays=-1):
        song.channel = self
        self.current_song = song
        self.channel.set_current_song(song, num_plays)
        self.battle.set_current_song(song, num_plays)

    def crossfade(self):
        if self.battle_mode:
            self.battle_mode = False
            self.channel.crossfade_in()
            self.battle.crossfade_out()
        else:
            self.battle_mode = True
            self.channel.crossfade_out()
            self.battle.crossfade_in()

    def clear(self):
        if self.current_song:
            self.current_song.channel = None
        self.current_song = None
        self.channel.clear()
        self.battle.clear()

    def fade_in(self):
        self.channel.fade_in()
        self.battle.fade_in()

    def fade_out(self):
        self.channel.fade_out()
        self.battle.fade_out()

    def pause(self):
        self.channel.pause()
        self.battle.pause()

    def resume(self):
        self.channel.resume()
        self.battle.resume()

    def stop(self):
        self.channel.stop()
        self.battle.stop()

    def set_volume(self, volume):
        self.channel.set_volume(volume)
        self.battle.set_volume(volume)

class SoundController():
    def __init__(self):
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(8)  # Reserve the first 8 channels for music
        self.global_music_volume = 1.0
        self.global_sfx_volume = 1.0

        self.channel1 = ChannelPair(0)
        self.channel2 = ChannelPair(2)  # Skip each time because battle channel
        self.channel3 = ChannelPair(4)
        self.channel4 = ChannelPair(6)

        self.channel_stack = [self.channel1, self.channel2, self.channel3, self.channel4]
        self.song_stack = []

        self.fade_out_start = 0
        self.fade_out_stop = 0

    @property
    def current_channel(self):
        return self.channel_stack[-1]

    def clear(self):
        self.stop()
        for channel in self.channel_stack:
            channel.clear()
        self.song_stack.clear()

    def fade_clear(self):
        self.current_channel.fade_out()
        self.fade_out_stop = engine.get_time()
        self.song_stack.clear()

    def fade_to_stop(self):
        self.current_channel.fade_out()
        self.fade_out_stop = engine.get_time()

    def pause(self):
        self.current_channel.pause()

    def resume(self):
        self.current_channel.resume()

    def mute(self):
        self.current_channel.set_volume(0)

    def get_music_volume(self):
        return self.global_music_volume

    def set_music_volume(self, volume):
        self.global_music_volume = volume
        for channel in self.channel_stack:
            channel.set_volume(self.global_music_volume)

    def get_sfx_volume(self):
        return self.global_sfx_volume

    def set_sfx_volume(self, volume):
        self.global_sfx_volume = volume

    def is_playing(self):
        return self.current_channel.is_playing()

    def set_next_song(self, song, num_plays):
        # Clear the oldest channel and use it
        # to play the next song
        oldest_channel = self.channel_stack[0]
        oldest_channel.clear()
        self.channel_stack.remove(oldest_channel)
        self.channel_stack.append(oldest_channel)
        oldest_channel.set_current_song(song, num_plays)

    def crossfade(self):
        self.current_channel.crossfade()

    def fade_in(self, next_song, num_plays=-1):
        logger.info("Fade in %s" % next_song)
        next_song = MUSIC.get(next_song)

        if self.is_playing():
            current_song = self.song_stack[-1]
        else:
            current_song = None

        # Confirm that we're not just replacing the same song
        if current_song is next_song:
            logger.info("Song already present")
            return None

        # Fade out the current channel
        self.current_channel.fade_out()
        self.fade_out_start = engine.get_time()

        # Determine if song is already in stack
        for song in self.song_stack:
            # If so, move to top of stack
            if song is next_song:
                logger.info("Pull up %s" % next_song)
                self.song_stack.remove(song)
                self.song_stack.append(song)
                # If we can use our old channel
                if song.channel and song.channel.current_song == song:
                    # Move to top
                    self.channel_stack.remove(song.channel)
                    self.channel_stack.append(song.channel)
                    song.channel.num_plays = num_plays
                else:
                    self.set_next_song(song, num_plays)
                break
        else:
            logger.info("New song %s" % next_song)
            self.song_stack.append(next_song)
            # Clear the oldest channel and use it
            self.set_next_song(next_song, num_plays)

        return self.song_stack[-1]

    def fade_back(self):
        logger.info("Fade back")

        if not self.song_stack:
            return
        current_channel = self.current_channel
        current_channel.fade_out()
        last_song = self.song_stack.pop()
        next_song = self.song_stack[-1] if self.song_stack else None
        # Move current channel down to bottom of world
        self.channel_stack.remove(current_channel)
        self.channel_stack.insert(0, current_channel)

    def stop(self):
        self.current_channel.stop()

    def update(self, event_list):
        current_time = engine.get_time()

        any_changes = False
        for channel in self.channel_stack:
            if channel.update(event_list, current_time):
                any_changes = True

        if self.fade_out_start and any_changes:
            self.fade_out_start = 0
            self.current_channel.set_volume(self.global_music_volume)
            self.current_channel.fade_in()
        elif self.fade_out_stop and any_changes:
            self.fade_out_stop = 0
            self.stop()

    def play_sfx(self, sound, loop=False):
        sfx = SFX.get(sound)
        if sfx:
            if sound == 'Select 5':
                # Cursor sound is muted
                sfx.set_volume(self.global_sfx_volume * .5)
            else:
                sfx.set_volume(self.global_sfx_volume)
            if loop:
                sfx.play(-1)
            else:
                sfx.play()
            return sfx
        return None

    def stop_sfx(self, sound):
        sfx = SFX.get(sound)
        if sfx:
            sfx.stop()
            return sfx
        return None

SOUNDTHREAD = SoundController()
