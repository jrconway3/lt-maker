from app.constants import COLORKEY
from app.engine.sprites import SPRITES
import os
import time
from enum import Enum

import pygame
import pygame.draw
import pygame.event
from pygame import Surface
from pygame import Color

from .demo_code.demo_cursor import Cursor, Scene
from .demo_code.demo_ui import DemoUI
from .premade_components.text_component import *
from .ui_framework import *
from .ui_framework_animation import *
from .ui_framework_layout import *
from .ui_framework_styling import *
from .premade_components import *
from .premade_animations import *

TILEWIDTH, TILEHEIGHT = 16, 16
TILEX, TILEY = 15, 10
WINWIDTH, WINHEIGHT = TILEX * TILEWIDTH, TILEY * TILEHEIGHT
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

def current_milli_time():
    return round(time.time() * 1000)

class Mode(Enum):
    OverworldUIMode = 0
    NarrationMode = 1


def main():
    screen = pygame.display.set_mode((WINWIDTH * 2, WINHEIGHT * 2))
    tmp_surf = pygame.Surface((WINWIDTH, WINHEIGHT))
    clock = pygame.time.Clock()
    
    mode = Mode.OverworldUIMode
    
    cursor = Cursor()
    world_map = pygame.image.load(os.path.join(DIR_PATH, 'demo_code', 'magvel_demo.png'))
    nodes = Scene()
    ui_overlay = DemoUI(cursor)
    cursor.scene = nodes
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return
                elif e.key == pygame.K_SPACE:
                    if mode == Mode.OverworldUIMode:
                        mode = Mode.NarrationMode
                        ui_overlay.narration.enter()
                    else:
                        ui_overlay.narration.scroll_to_next()
                elif e.key == pygame.K_BACKSPACE:
                    if mode == Mode.NarrationMode:
                        ui_overlay.narration.exit()
                        mode = Mode.OverworldUIMode
                elif e.key == pygame.K_TAB:
                    if mode == Mode.NarrationMode:
                        ui_overlay.narration.write_a_line()
            cursor.take_input(events)
        tmp_surf.blit(world_map, (0, 0))
        nodes.draw(tmp_surf)
        cursor.draw(tmp_surf)
        ui_overlay.draw(tmp_surf)
        frame = pygame.transform.scale(tmp_surf, (WINWIDTH * 2, WINHEIGHT * 2))
        screen.blit(frame, (0, 0))
        pygame.display.flip()
        clock.tick(60)

"""Usage: python -m app.engine.graphics.ui_framework.demo"""
main()
