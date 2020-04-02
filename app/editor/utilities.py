from PyQt5 import QtGui

from app.data.constants import COLORKEY

qCOLORKEY = QtGui.qRgb(*COLORKEY)
qAlpha = QtGui.qRgba(0, 0, 0, 0)

def convert_colorkey_slow(image):
    image.convertTo(QtGui.QImage.Format_ARGB32)
    for x in range(image.width()):
        for y in range(image.height()):
            if image.pixel(x, y) == qCOLORKEY:
                image.setPixel(x, y, qAlpha)
    return image

def convert_colorkey(image):
    image.convertTo(QtGui.QImage.Format_Indexed8)
    for i in range(image.colorCount()):
        if image.color(i) == qCOLORKEY:
            image.setColor(0, qAlpha)
    return image

enemy_colors = {(56, 56, 144): (96, 40, 32),
                (56, 80, 224): (168, 48, 40),
                (40, 160, 248): (224, 16, 16),
                (24, 240, 248): (248, 80, 72),
                (232, 16, 24): (56, 208, 48),
                (88, 72, 120): (104, 72, 96),
                (216, 232, 240): (224, 224, 224),
                (144, 184, 232): (192, 168, 184)}

other_colors = {(56, 56, 144): (32, 80, 16),
                (56, 80, 224): (8, 144, 0),
                (40, 160, 248): (24, 208, 16),
                (24, 240, 248): (80, 248, 56),
                (232, 16, 24): (0, 120, 200),
                (88, 72, 120): (56, 80, 56),
                (144, 184, 232): (152, 200, 158),
                (216, 232, 240): (216, 248, 184),
                (112, 96, 96): (88, 88, 80),
                (176, 144, 88): (160, 136, 64),
                (248, 248, 208): (248, 248, 192),
                (248, 248, 64): (224, 248, 40)}

enemy2_colors = {(56, 56, 144): (88, 32, 96),
                 (56, 80, 224): (128, 48, 144),
                 (40, 160, 248): (184, 72, 224),
                 (24, 240, 248): (208, 96, 248),
                 (232, 16, 24): (56, 208, 48),
                 (88, 72, 120): (88, 64, 104),
                 (144, 184, 232): (168, 168, 232),
                 (64, 56, 56): (72, 40, 64)}

enemy_colors = {QtGui.qRgb(*k): QtGui.qRgb(*v) for k, v in enemy_colors.items()}
other_colors = {QtGui.qRgb(*k): QtGui.qRgb(*v) for k, v in other_colors.items()}
enemy2_colors = {QtGui.qRgb(*k): QtGui.qRgb(*v) for k, v in enemy2_colors.items()}

def color_convert_slow(image, conversion_dict):
    for x in range(image.width()):
        for y in range(image.height()):
            current_color = image.pixel(x, y)
            if current_color in conversion_dict:
                new_color = conversion_dict[current_color]
                image.setPixel(x, y, new_color)
    return image

def color_convert(image, conversion_dict):
    for old_color, new_color in conversion_dict.items():
        for i in range(image.colorCount()):
            if image.color(i) == old_color:
                image.setColor(i, new_color)
    return image
