#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

WHITE = QColor(255, 255, 255)
BLACK = QColor(0, 0, 0)
RED = QColor(255, 0, 0)
PRIMARY = QColor(53, 53, 53, 232)
SECONDARY = QColor(35, 35, 35, 232)
TERTIARY = QColor(42, 130, 218, 232)
DISABLED = QColor(128, 128, 128)

DISPRIMARY = QColor(54, 57, 63)
DISSECONDARY = QColor(47, 49, 54)
DISTERTIARY = QColor(57, 60, 67)
GRAY = QColor(230, 230, 225)

TRANSPRIMARY = QColor(53, 53, 53, 232)
TRANSSECONDARY = QColor(35, 35, 35, 232)
TRANSTERTIARY = QColor(42, 130, 218, 232)

BLUEPRIMARY = QColor(91, 105, 117, 232)
BLUESECONDARY = QColor(69, 66, 89, 232)
BLUETERTIARY = QColor(128, 143, 137, 232)

def css_rgb(color, a=False):
    """Get a CSS `rgb` or `rgba` string from a `QtGui.QColor`."""
    return ("rgba({}, {}, {}, {})" if a else "rgb({}, {}, {})").format(*color.getRgb())

class QDarkPalette(QPalette):
    """Dark palette for a Qt application meant to be used with the Fusion theme."""
    def __init__(self, *__args):
        super().__init__(*__args)

        # Set all the colors based on the constants in globals
        self.setColor(QPalette.Window, PRIMARY)
        self.setColor(QPalette.WindowText, WHITE)
        self.setColor(QPalette.Base, SECONDARY)
        self.setColor(QPalette.AlternateBase, PRIMARY)
        self.setColor(QPalette.ToolTipBase, WHITE)
        self.setColor(QPalette.ToolTipText, WHITE)
        self.setColor(QPalette.Text, WHITE)
        self.setColor(QPalette.Button, PRIMARY)
        self.setColor(QPalette.ButtonText, WHITE)
        self.setColor(QPalette.BrightText, RED)
        self.setColor(QPalette.Link, TERTIARY)
        self.setColor(QPalette.Highlight, TERTIARY)
        self.setColor(QPalette.HighlightedText, BLACK)

        self.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.Text, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED)

    @staticmethod
    def set_stylesheet(app):
        """Static method to set the tooltip stylesheet to a `QtWidgets.QApplication`."""
        app.setStyleSheet("QToolTip {{"
                          "color: {white};"
                          "background-color: {tertiary};"
                          "border: 1px solid {white};"
                          "}}".format(white=css_rgb(WHITE), tertiary=css_rgb(TERTIARY)))

    def set_app(self, app):
        """Set the Fusion theme and this palette to a `QtWidgets.QApplication`."""
        app.setStyle("Fusion")
        app.setPalette(self)
        self.set_stylesheet(app)

class QDiscordPalette(QDarkPalette):
    def __init__(self, *__args):
        super().__init__(*__args)

        # Set all the colors based on the constants in globals
        self.setColor(QPalette.Window, DISPRIMARY)
        self.setColor(QPalette.WindowText, GRAY)
        self.setColor(QPalette.Base, DISSECONDARY)
        self.setColor(QPalette.AlternateBase, DISPRIMARY)
        self.setColor(QPalette.ToolTipBase, WHITE)
        self.setColor(QPalette.ToolTipText, GRAY)
        self.setColor(QPalette.Text, GRAY)
        self.setColor(QPalette.Button, DISPRIMARY)
        self.setColor(QPalette.ButtonText, WHITE)
        self.setColor(QPalette.BrightText, RED)
        self.setColor(QPalette.Link, DISTERTIARY)
        self.setColor(QPalette.Highlight, DISTERTIARY)
        self.setColor(QPalette.HighlightedText, WHITE)

        self.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.Text, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED)

class QDarkBGPalette(QDarkPalette):
    """Dark palette for a Qt application meant to be used with the Fusion theme."""
    def __init__(self, *__args):
        super().__init__(*__args)

        # Set all the colors based on the constants in globals
        self.setColor(QPalette.Window, TRANSPRIMARY)
        self.setColor(QPalette.WindowText, WHITE)
        self.setColor(QPalette.Base, TRANSSECONDARY)
        self.setColor(QPalette.AlternateBase, TRANSPRIMARY)
        self.setColor(QPalette.ToolTipBase, WHITE)
        self.setColor(QPalette.ToolTipText, WHITE)
        self.setColor(QPalette.Text, WHITE)
        self.setColor(QPalette.Button, TRANSPRIMARY)
        self.setColor(QPalette.ButtonText, WHITE)
        self.setColor(QPalette.BrightText, RED)
        self.setColor(QPalette.Link, TRANSTERTIARY)
        self.setColor(QPalette.Highlight, TRANSTERTIARY)
        self.setColor(QPalette.HighlightedText, BLACK)

        self.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.Text, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED)

class QBlueBGPalette(QDarkPalette):
    """Dark palette for a Qt application meant to be used with the Fusion theme."""
    def __init__(self, *__args):
        super().__init__(*__args)

        # Set all the colors based on the constants in globals
        self.setColor(QPalette.Window, BLUEPRIMARY)
        self.setColor(QPalette.WindowText, WHITE)
        self.setColor(QPalette.Base, BLUESECONDARY)
        self.setColor(QPalette.AlternateBase, BLUEPRIMARY)
        self.setColor(QPalette.ToolTipBase, WHITE)
        self.setColor(QPalette.ToolTipText, WHITE)
        self.setColor(QPalette.Text, WHITE)
        self.setColor(QPalette.Button, BLUEPRIMARY)
        self.setColor(QPalette.ButtonText, WHITE)
        self.setColor(QPalette.BrightText, RED)
        self.setColor(QPalette.Link, BLUETERTIARY)
        self.setColor(QPalette.Highlight, BLUETERTIARY)
        self.setColor(QPalette.HighlightedText, BLACK)

        self.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.Text, DISABLED)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED)
