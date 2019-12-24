from PyQt5 import QtGui

from app.data.constants import COLORKEY

def convert_colorkey(image):
    image.convertTo(QtGui.QImage.Format_ARGB32)
    qCOLORKEY = QtGui.qRgb(*COLORKEY)
    new_color = QtGui.qRgba(0, 0, 0, 0)
    for x in range(image.width()):
        for y in range(image.height()):
            if image.pixel(x, y) == qCOLORKEY:
                image.setPixel(x, y, new_color)
    return image
