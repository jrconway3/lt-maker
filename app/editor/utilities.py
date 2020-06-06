from PyQt5 import QtGui

from app.data.constants import COLORKEY
from app.data.palettes import enemy_colors, other_colors, enemy2_colors

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
            image.setColor(i, qAlpha)
            break
    return image

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

def find_palette(image):
    palette = []
    for x in range(image.width()):
        for y in range(image.height()):
            current_color = image.pixel(x, y)
            if current_color not in palette:
                palette.append(current_color)
    return palette
