class State():
    name = None
    in_level = True
    show_map = True
    transparent = False

    started = False
    processed = False

    def __init__(self, name=None):
        if name:
            self.name = name

    def start(self):
        pass

    def begin(self):
        pass

    def take_input(self, events):
        pass

    def update(self):
        pass

    def draw(self):
        return None

    def end(self):
        pass

    def finish(self):
        pass
