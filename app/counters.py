# Helper global object for map sprite animations
class generic3counter():
    def __init__(self, first_time=440, second_time=50, third_time=None):
        self.count = 0
        self.last_update = 0
        self.lastcount = 1
        self.first_time = int(first_time)
        self.second_time = int(second_time)
        self.third_time = self.first_time if third_time is None else int(third_time)
        
    def update(self, current_time):
        if self.count == 1 and current_time - self.last_update > self.second_time:
            self.increment()
            self.last_update = current_time
            return True
        elif self.count == 0 and current_time - self.last_update > self.first_time:
            self.increment()
            self.last_update = current_time
            return True
        elif self.count == 2 and current_time - self.last_update > self.third_time:
            self.increment()
            self.last_update = current_time
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

class simplecounter():
    def __init__(self, times):
        self.count = 0
        self.times = times
        self.last_update = 0

    def update(self, current_time):
        if current_time - self.last_update > self.times[self.count]:
            self.count = (self.count + 1) % len(self.times)
            self.last_update = current_time
            return True
        return False
