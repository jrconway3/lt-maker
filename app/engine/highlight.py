from app.data.constants import TILEWIDTH, TILEHEIGHT
from app.engine.sprites import SPRITES
from app.engine import engine
from app.engine.game_state import game

import logging
logger = logging.getLogger(__name__)

# class Highlight():
#     def __init__(self, spritename):
#         self.sprite = SPRITES.get(spritename)
#         self.image = None

#     def draw(self, surf, position, idx, transition):
#         pass

class HighlightController():
    starting_cutoff = 7

    def __init__(self):
        self.images = {'spell': SPRITES.get('highlight_green'),
                       'attack': SPRITES.get('highlight_red'),
                       'splash': SPRITES.get('highlight_lightred'),
                       'possible_move': SPRITES.get('highlight_lightblue'),
                       'move': SPRITES.get('highlight_blue'),
                       'aura': SPRITES.get('highlight_lightpurple'),
                       'spell_splash': SPRITES.get('highlight_lightpurple')}

        self.highlights = {k: set() for k in self.images}
        self.transitions = {k: self.starting_cutoff for k in self.images}

        self.last_update = 0
        self.update_idx = 0

        self.current_hover = None

    def add_highlight(self, position, name, allow_overlap=False):
        if not allow_overlap:
            for k in self.images:
                self.highlights[k].discard(position)
        self.highlights[name].add(position)
        self.transitions[name] = self.starting_cutoff

    def add_highlights(self, positions: set, name: str, allow_overlap: bool = False):
        if not allow_overlap:
            for k in self.images:
                self.highlights[k] -= positions
        self.highlights[name] |= positions
        self.transitions[name] = self.starting_cutoff

    def remove_highlights(self, name=None):
        if name:
            self.highlights[name].clear()
            self.transitions[name] = self.starting_cutoff
        else:
            for k in self.images:
                self.highlights[k].clear()
                self.transitions[k] = self.starting_cutoff
        self.current_hover = None

    def remove_aura_highlights(self):
        self.highlights['aura'].clear()

    def handle_hover(self):
        hover_unit = game.cursor.get_hover()
        if self.current_hover and hover_unit != self.current_hover:
            self.remove_highlights()
        if hover_unit and hover_unit != self.current_hover:
            valid_moves = game.targets.get_valid_moves(hover_unit)
            if hover_unit.get_spell():
                valid_attacks = game.targets.get_possible_spell_attacks(hover_unit, valid_moves)
                self.display_possible_spell_attacks(valid_attacks, light=True)
            if hover_unit.get_weapon():
                valid_attacks = game.targets.get_possible_attacks(hover_unit, valid_moves)
                self.display_possible_attacks(valid_attacks, light=True)
            self.display_moves(valid_moves, light=True)
            # Aura.add_aura_highlights(hover_unit)
        self.current_hover = hover_unit

    def display_moves(self, valid_moves, light=False):
        name = 'possible_move' if light else 'move'
        self.add_highlights(valid_moves, name)

    def display_possible_attacks(self, valid_attacks, light=False):
        name = 'splash' if light else 'attack'
        self.add_highlights(valid_attacks, name)

    def display_possible_spell_attacks(self, valid_attacks, light=False):
        name = 'spell_splash' if light else 'spell'
        self.add_highlights(valid_attacks, name)

    def update(self):
        self.update_idx = (self.update_idx + 1) % 64

    def draw(self, surf):
        for name, highlight_set in self.highlights.items():
            if not highlight_set:
                continue
            self.transitions[name] = max(0, self.transitions[name] - 1)
            cut_off = self.transitions[name]
            rect = (self.update_idx//4 * TILEWIDTH + cut_off, cut_off, TILEWIDTH - cut_off, TILEHEIGHT - cut_off)
            image = engine.subsurface(self.images[name], rect)
            for position in highlight_set:
                surf.blit(image, (position[0] * TILEWIDTH, position[1] * TILEHEIGHT))
        return surf
