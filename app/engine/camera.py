from app.data.constants import TILEX, TILEY
from app.engine.game_state import game

class Camera():
    def __init__(self):
        # Where the camera is going
        self.target_x = 0
        self.target_y = 0
        # Where the camera actually is
        self.current_x = 0
        self.current_y = 0

        # How fast the camera should move
        self.speed = 8.0  # Linear speed based on distance from target

        # Whether the camera should be panning at a constant speed
        self.pan_mode = False
        self.pan_speed = 0.125  
        self.pan_targets = []

    def set_x(self, x):
        self.target_x = x

    def set_y(self, y):
        self.target_y = y

    def set_xy(self, x, y):
        self.target_x = x
        self.target_y = y

    def force_x(self, x):
        self.current_x = self.target_x = x

    def force_y(self, y):
        self.current_y = self.target_y = y

    def force_xy(self, x, y):
        self.current_x = self.target_x = x
        self.current_y = self.target_y = y

    def get_x(self):
        return self.current_x

    def get_y(self):
        return self.current_y

    def get_xy(self):
        return self.current_x, self.current_y

    def at_rest(self):
        return self.current_x == self.target_x and self.current_y == self.target_y

    def set_target_limits(self, tilemap):
        if self.target_x < 0:
            self.target_x = 0
        elif self.target_x > tilemap.width - TILEX:
            self.target_x = tilemap.width - TILEX
        if self.target_y < 0:
            self.target_y = 0
        elif self.target_y > tilemap.height - TILEY:
            self.target_y = tilemap.height - TILEY

    def set_current_limits(self, tilemap):
        if self.current_x < 0:
            self.current_x = 0
        elif self.current_x > tilemap.width - TILEX:
            self.current_x = tilemap.width - TILEX
        if self.current_y < 0:
            self.current_y = 0
        elif self.current_y > tilemap.height - TILEY:
            self.current_y = tilemap.height - TILEY

    def update(self):
        # Make sure target is within bounds
        self.set_target_limits(game.tilemap)

        # Move camera around
        diff_x = self.target_x - self.current_x
        if diff_x > 0:
            self.current_x += self.pan_speed if self.pan_mode else diff_x/self.speed
        elif diff_x < 0:
            self.current_x += -self.pan_speed if self.pan_mode else diff_x/self.speed
        diff_y = self.target_y- self.current_y
        if diff_y > 0:
            self.current_y += self.pan_speed if self.pan_mode else diff_y/self.speed
        elif diff_y < 0:
            self.current_y += -self.pan_speed if self.pan_mode else diff_y/self.speed

        # If close enough to target, just make it so
        if abs(diff_x) < 0.25:
            self.current_x = self.target_x
        if abs(diff_y) < 0.25:
            self.current_y = self.target_y

        if self.pan_targets and self.at_rest():
            self.target_x, self.target_y = self.pan_targets.pop()

        # Make sure we do not go offscreen -- maybe shouldn't happen?
        # Could happen when map size changes?
        self.set_current_limits(game.tilemap)
