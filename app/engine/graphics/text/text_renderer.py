from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.engine import engine
from app.engine.fonts import FONT
from app.engine.icons import draw_icon_by_alias
from app.utilities.typing import NID

tag_match = re.compile('<(.*?)>')

def rendered_text_width(fonts: List[NID], texts: List[str]) -> int:
    """Returns the full rendered width (see render_text) of a text list.

    Args:
        fonts (List[NID]): List of fonts to use to write text.
        texts (List[str]): List of strings to write with corresponding fonts.

    Returns:
        int: _description_
    """
    if not fonts:
        return
    if not texts:
        return
    font_stack = fonts[:]
    font_stack.reverse()
    text_stack = texts[:]
    text_stack.reverse()

    base_font = fonts[-1]
    font_history_stack = []
    total_width = 0
    while(text_stack):
        curr_text = text_stack.pop()
        curr_font = font_stack.pop()
        # don't pop if this is the last font
        if not font_stack:
            font_stack.append(curr_font)
        # process text for tags and push them onto stack for later processing
        any_tags = tag_match.search(curr_text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag_font = any_tags.group().strip("<>")
            if tag_font == '/':
                tag_font = font_history_stack.pop() if font_history_stack else base_font
            else:
                font_history_stack.append(curr_font)
            text_stack.append(curr_text[tag_end:])
            curr_text = curr_text[:tag_start]
            if tag_font in FONT or tag_font == 'icon':
                font_stack.append(tag_font)
            else:
                font_stack.append(curr_font)
        # actually render font
        if curr_font != 'icon':
            total_width += FONT[curr_font].width(curr_text)
        else:
            total_width += 16
    return total_width

def render_text(surf: engine.Surface, fonts: List[NID], texts: List[str], colors: List[NID], topleft: Tuple[int, int]) -> engine.Surface:
    """An enhanced text render layer wrapper around BmpFont.
    Supports multiple fonts and multiple text sections, as well as
    embedded icons.

    Args:
        fonts (List[NID]): List of fonts to use to write text.
        texts (List[str]): List of strings to write with corresponding fonts.
        colors (List[str]): List of colors to write with corresponding fonts.

    Returns:
        engine.Surface: a surface that has text printed upon it.
    """
    if not fonts:
        return
    if not texts:
        return
    if not colors:
        colors = [None]
    font_stack = fonts[:]
    font_stack.reverse()
    text_stack = texts[:]
    text_stack.reverse()
    color_stack = colors[:]
    color_stack.reverse()

    base_font = fonts[-1]
    font_history_stack = []
    tx, ty = topleft
    while(text_stack):
        curr_text = text_stack.pop()
        curr_font = font_stack.pop()
        curr_color = color_stack.pop() if color_stack else None
        # don't pop if this is the last font
        if not font_stack:
            font_stack.append(curr_font)
        if not color_stack:
            color_stack.append(curr_color)
        # process text for tags and push them onto stack for later processing
        any_tags = tag_match.search(curr_text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag_font = any_tags.group().strip("<>")
            if tag_font == '/':
                tag_font, tag_color = font_history_stack.pop() if font_history_stack else base_font
            else:
                if tag_font in FONT or tag_font == 'icon':
                    tag_color = curr_color
                else:
                    tag_color = tag_font
                    tag_font = curr_font
                font_history_stack.append((curr_font, curr_color))
            text_stack.append(curr_text[tag_end:])
            curr_text = curr_text[:tag_start]
            font_stack.append(tag_font)
            color_stack.append(tag_color)
        # actually render font
        if curr_font != 'icon':
            FONT[curr_font].blit(curr_text, surf, (tx, ty), curr_color)
            tx += FONT[curr_font].width(curr_text)
        else:
            draw_icon_by_alias(surf, curr_text.strip(), (tx, ty))
            tx += 16
    return surf
