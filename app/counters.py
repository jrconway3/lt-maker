# Helper global object for map sprite animations
class generic3counter(object):
    def __init__(self, first_time=440, second_time=50, third_time=None):
        self.count = 0
        self.lastUpdate = 0
        self.lastcount = 1
        self.first_time = first_time
        self.second_time = second_time
        self.third_time = self.first_time if third_time is None else third_time
        
    def update(self, current_time):
        if self.count == 1 and current_time - self.lastUpdate > self.second_time:
            self.increment()
            self.lastUpdate = current_time
            return True
        elif self.count == 0 and current_time - self.lastUpdate > self.first_time:
            self.increment()
            self.lastUpdate = current_time
            return True
        elif self.count == 2 and current_time - self.lastUpdate > self.third_time:
            self.increment()
            self.lastUpdate = current_time
            return True
        return False

    def increment(self):
        if self.count == 0:
            self.count = 1
            self.lastcount = 0
        elif self.count == 2:
            self.count = 1
            self.lastcount = 2
        else:
            if self.lastcount == 0:
                self.count = 2
                self.lastcount = 1
            elif self.lastcount == 2:
                self.count = 0
                self.lastcount = 1
