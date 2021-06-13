import os
import time
from enum import Enum

import pygame
import pygame.draw
import pygame.event
from pygame import Surface
from pygame import Color

from app.constants import COLORKEY
from app.engine.sprites import SPRITES
pygame.mixer.init()
from app.engine.dialog import Dialog
from app.engine.dialog_log import *

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

def add_dummy_logs(log_obj):
    speak_commands = [
    "speak;Seth;Princess Eirika! This way! I can see no more of Grado's men.|If we've made it this far, we've surely earned a moment's rest.|Please forgive my grabbing you so...brusquely earlier.",
    "speak;Eirika;Don't be foolish, Seth.|If it weren't for you, I would never have made it out of the castle.|You are the reason I'm still alive. You have my gratitude.",
    "speak;Eirika;And whoever that man was, he was clearly after me...|It's my fault that you received such a grave wound.|Allow me to treat it, I--",
    "speak;Seth;Your Highness, I can't allow an injury like this to be an obstacle.|We have more important matters to attend to. We must press on to Frelia.|We must fulfill His Majesty's wishes.",
    "speak;Eirika;...|I wonder how my father fares alone in the castle. Do you think he's safe?|And what of my brother on the Grado front? We've heard nothing from him for days.",
    "speak;Seth;King Fado and Prince Ephraim are both valiant and brave men.|I doubt even the might of the Grado Empire can hold them in check.|More important to me, Your Highness, is that you look to your own safety.|How sad the two of them would be if something were to happen to you.|We must reach Frelia to ensure the day of your happy reunion.",
    "speak;Eirika;Yes, of course. You're right.|Until I'm reunited with my father and brother, I must not despair.|Come, Seth. Let us go."
    ]

    for command in speak_commands:
        command = command.replace('speak;','').split(';')
        dialog = Dialog(command[1], speaker=command[0])
        log_obj.log_dialog(dialog)

def main():
    screen = pygame.display.set_mode((WINWIDTH * 2, WINHEIGHT * 2))
    tmp_surf = pygame.Surface((WINWIDTH, WINHEIGHT))
    clock = pygame.time.Clock()

    world_map = pygame.image.load(os.path.join(DIR_PATH, 'demo_code', 'magvel_demo.png'))

    dialog_history = DialogLog()
    add_dummy_logs(dialog_history)

    show_log = False
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return
                elif e.key == pygame.K_SPACE:
                    show_log = not show_log
                    if show_log:
                        dialog_history.ui.enter()

        tmp_surf.blit(world_map, (0, 0))

        if show_log:
            dialog_history.draw(tmp_surf)

        frame = pygame.transform.scale(tmp_surf, (WINWIDTH * 2, WINHEIGHT * 2))
        screen.blit(frame, (0, 0))
        pygame.display.flip()
        clock.tick(60)

"""Usage: python -m app.engine.graphics.ui_framework.dialog_log_demo.py"""
main()
