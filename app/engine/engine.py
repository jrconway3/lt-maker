import sys

import pygame

from app.engine import config as cf

import logging
logger = logging.getLogger(__name__)

constants = {'current_time': 0,
             'last_time': 0,
             'last_fps': 0}

# === engine functions ===
def init():
    pygame.mixer.pre_init(44100, -16, 2, 256 * 2**cf.SETTINGS['sound_buffer_size'])
    pygame.init()
    pygame.mixer.init()

def simple_init():
    pygame.init()

def set_icon(icon):
    pygame.display.set_icon(icon)

def set_title(text):
    pygame.display.set_caption(text)

def build_display(size):
    return pygame.display.set_mode(size)

def push_display(surf, size, new_surf):
    pygame.transform.scale(surf, size, new_surf)

def update_display():
    pygame.display.update()

def remove_display():
    pygame.display.quit()

def terminate(crash=False):
    on_end(crash)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

def on_end(crash=False):
    # Edit screen size
    if 'temp_screen_size' in cf.SETTINGS:
        cf.SETTINGS['screen_size'] = cf.SETTINGS['temp_screen_size']
    cf.save_settings()

# === timing functions ===
def update_time():
    constants['last_time'] = constants['current_time']
    constants['current_time'] = pygame.time.get_ticks()
    constants['last_fps'] = constants['current_time'] - constants['last_time']

def get_time():
    return constants['current_time']

def get_last_time():
    return constants['last_time']

def get_true_time():
    return pygame.time.get_ticks()

def get_delta():
    return constants['last_fps']

# === drawing functions ===
BLEND_RGB_ADD = pygame.BLEND_RGB_ADD
BLEND_RGB_SUB = pygame.BLEND_RGB_SUB
BLEND_RGB_MULT = pygame.BLEND_RGB_MULT
BLEND_RGBA_ADD = pygame.BLEND_RGBA_ADD
BLEND_RGBA_SUB = pygame.BLEND_RGBA_SUB
BLEND_RGBA_MULT = pygame.BLEND_RGBA_MULT

def blit(dest, source, pos=(0, 0), mask=None, blend=0):
    dest.blit(source, pos, mask, blend)

def create_surface(size, transparent=False):
    if transparent:
        surf = pygame.Surface(size, pygame.SRCALPHA, 32)
        surf = surf.convert_alpha()
    else:
        surf = pygame.Surface(size)
        surf = surf.convert()
    return surf

def copy_surface(surf):
    return surf.copy()

def save_surface(surf, fn):
    pygame.image.save(surf, fn)

def subsurface(surf, rect):
    x, y, width, height = rect
    return surf.subsurface(x, y, width, height)

def image_load(fn, convert=False, convert_alpha=False):
    image = pygame.image.load(fn)
    if convert:
        image = image.convert()
    elif convert_alpha:
        image = image.convert_alpha()
    return image

def fill(surf, color, mask=None, blend=0):
    surf.fill(color, mask, blend)

def set_alpha(surf, alpha, rleaccel=False):
    if rleaccel:
        surf.set_alpha(alpha, pygame.RLEACCEL)
    else:
        surf.set_alpha(alpha)

def set_colorkey(surf, color, rleaccel=True):
    if rleaccel:
        surf.set_colorkey(color, pygame.RLEACCEL)
    else:
        surf.set_colorkey(color)

# === transform functions ===
def flip_horiz(surf):
    return pygame.transform.flip(surf, 1, 0)

def flip_vert(surf):
    return pygame.transform.flip(surf, 0, 1)

def transform_scale(surf, scale):
    return pygame.transform.scale(surf, scale)

def transform_rotate(surf, degrees):
    return pygame.transform.rotate(surf, degrees)

# === event functions ===
def get_key_name(key_code):
    return pygame.key.name(key_code)

def get_events():
    events = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        if event.type == pygame.KEYDOWN and cf.SETTINGS['debug']:
            if event.key == pygame.K_ESCAPE:
                terminate()
        events.append(event)
    return events

# === controls functions ===
KEYUP = pygame.KEYUP
KEYDOWN = pygame.KEYDOWN
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
MOUSEMOTION = pygame.MOUSEMOTION

def get_pressed():
    return pygame.key.get_pressed()

def joystick_avail():
    return pygame.joystick.get_count()

def get_joystick():
    return pygame.joystick.Joystick(0)
