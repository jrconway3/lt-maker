import time

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, pyqtSignal

import app.data.constants as constants
from app import counters

class Timer(QWidget):
    tick_elapsed = pyqtSignal()

    def __init__(self, fps=60):
        super().__init__()
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.tick)
        timer_speed = int(1000/float(fps))
        self.main_timer.setInterval(timer_speed)
        self.main_timer.start()

        framerate = constants.FRAMERATE
        self.passive_counter = counters.generic3counter(int(32*framerate), int(4*framerate))
        self.active_counter = counters.generic3counter(int(13*framerate), int(6*framerate))

    def tick(self):
        current_time = int(round(time.time() * 1000))
        self.passive_counter.update(current_time)
        self.active_counter.update(current_time)
        self.tick_elapsed.emit()

TIMER = Timer(constants.FPS)
