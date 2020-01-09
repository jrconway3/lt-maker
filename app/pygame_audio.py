import pygame

class PygameAudioPlayer(object):
    def __init__(self):
        self.initiated = False
        self.current = None
        self.display = None
        self.volume = 1.0
        self.current_position = 0  # In milliseconds
        self.duration = 0  # In milliseconds

    def initiate(self):
        pygame.mixer.pre_init(44100, -16, 2, 256 * 2**4)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        self.display = pygame.display.set_mode((1, 1))
        self.initiated = True

    def play(self, fn):
        """
        Returns whether the song was actually re-loaded or just unpaused
        """
        if not self.initiated:
            self.initiate()
        if self.current != fn:
            pygame.mixer.music.load(fn)
            my_sound = pygame.mixer.Sound(fn)
            self.duration = my_sound.get_length() * 1000
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
            self.current = fn
            self.current_position = 0
            print(fn, self.duration)
            return True
        else:
            pygame.mixer.music.unpause()
            return False

    def pause(self):
        pygame.mixer.music.pause()

    def stop(self):
        pygame.mixer.music.stop()
        self.current_position = 0
        self.current = None
        self.duration = 0

    def quit(self):
        if self.initiated:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.quit()

    def setVolume(self, vol):
        self.volume = vol

    def get_position(self):
        if self.current:
            return self.current_position + pygame.mixer.music.get_pos()
        else:
            return 0

    def set_position(self, val):
        if self.current:
            pygame.mixer.music.set_pos(val)
            self.current_position = val
