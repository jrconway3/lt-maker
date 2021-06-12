from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Union

from app.engine import engine, text_funcs
from app.engine.bmpfont import BmpFont
from app.engine.fonts import FONT
from app.engine.graphics.ui_framework.ui_framework_styling import UIMetric
from app.utilities.utils import clamp

if TYPE_CHECKING:
    from pygame import Surface

from ..ui_framework import ComponentProperties, ResizeMode, UIComponent


class TextProperties(ComponentProperties):
    """Properties that are particular to text-based components.
    """
    def __init__(self):
        super().__init__()
        self.font: BmpFont = FONT['text-white']         # self-explanatory: the font
        self.line_break_size: str = '0px'               # if the text component is multiline, how much space
                                                        # is between the two lines. Can be percentage or pixel value.

        self.max_lines: int = 2                         # maximum number of lines to split the text over, if max_width is set.

class TextComponent(UIComponent):
    """A component consisting purely of text
    """
    def __init__(self, name: str = "", text: str = "", parent: UIComponent = None):
        super().__init__(name=name, parent=parent)
        self.props: TextProperties = TextProperties()
        self.text = text
        self.num_visible_chars = len(text)
        self.final_formatted_text = []
        self.scrolled_line: float = 1
        self._recalculate_size()

    @property
    def font_height(self) -> int:
        return self.props.font.height

    @property
    def max_text_width(self) -> int:
        return UIMetric.parse(self.props.max_width).to_pixels(self.parent.width) - self.padding[0] - self.padding[1]

    @property
    def line_break_size(self) -> int:
        return UIMetric.parse(self.props.line_break_size).to_pixels(self.parent.height)

    def set_font(self, font: BmpFont):
        """Sets the font of this component and recalculates the component size.

        Args:
            font (BmpFont): font to use to draw the text
        """
        self.props.font = font
        self._recalculate_size()

    def set_line_break_size(self, line_break_size: str):
        """Sets the line break size of this component and recalculates the component size.

        Args:
            line_break_size (str): pixel or percentage measure for how much space is between
            the lines of text. Percentage measured in size of parent.
        """
        self.props.line_break_size = line_break_size
        self._recalculate_size()

    def set_num_lines(self, num_lines: int):
        """Sets the max lines of this component and recalculates the component size.

        Args:
            num_lines (int): max number of lines
        """
        self.props.max_lines = num_lines
        self._recalculate_size()

    # @overrides UIComponent.padding.setter
    @UIComponent.padding.setter
    def padding(self, padding: Tuple[int, int, int, int]):
        """sets an explicit pixel padding and recalculates the component size

        Args:
            padding (Tuple[int, int, int, int]): padding in pixels
        """
        self.ipadding = [UIMetric.parse(padding[0]),
                         UIMetric.parse(padding[1]),
                         UIMetric.parse(padding[2]),
                         UIMetric.parse(padding[3])]
        self._recalculate_size()

    def _recalculate_size(self):
        """Given our formatted text and our font, we can easily determine
        the size of the text component.
        """
        self._add_line_breaks_to_text()
        if self.props.resize_mode == ResizeMode.AUTO:
            num_lines = len(self.final_formatted_text)
            if num_lines == 1:
                # all text is on one line anyway, just go by text
                text_size = self.props.font.size(self.text)
            else:
                # if not, we can just do math with max width
                # and the number of lines plus number of breaks
                height = num_lines * self.font_height + (num_lines - 1) * self.line_break_size
                text_size = self.max_text_width, height
            self.size = (text_size[0] + 2 + self.padding[0] + self.padding[1],
                         text_size[1] + self.padding[2] + self.padding[3])

    def set_text(self, text: str):
        """Sets the text of this text component and recalculates the component size.

        Args:
            text (str): Text to display
        """
        self.text = text
        self.num_visible_chars = len(text)
        self._recalculate_size()

    def set_visible(self, num_chars_visible: int):
        """If you do not wish to display all the text at once,
        you can specify how many characters you want to display
        at any given time. Useful for dialog.

        Args:
            num_visible_chars (int): number of chars, starting from the beginning
            of the text, to display
        """
        self.num_visible_chars = num_chars_visible

    # @overrides UIComponent._create_bg_surf()
    def _create_bg_surf(self) -> Surface:
        """Generates an appropriately-sized text transparent background
        according to our size.

        Returns:
            Surface: a correctly-sized transparent surf.
        """
        # if we don't have cached, or our size has changed since last background generation, regenerate
        if not self.cached_background or self.cached_background.get_size() != self.size:
            self.cached_background = engine.create_surface(self.size, True)
        return self.cached_background

    def _add_line_breaks_to_text(self):
        """Generates correctly line-broken text based on
        our max width. This is stored in the internal list `final_formatted_text`
        """
        # determine the max length of the string we can fit on the first line
        # we will only split on spaces so as to preserve words on the same line
        if self.props.max_width:
            lines = text_funcs.line_wrap(self.props.font, self.text, self.max_text_width)
            self.final_formatted_text = lines
        else:
            self.final_formatted_text = [self.text]

    @property
    def scrollable_height(self):
        height_of_max_lines = self.props.max_lines * self.font_height + (self.props.max_lines - 1) * self.line_break_size
        return self.height - height_of_max_lines

    def _pixel_height_to_line(self, pixels):
        return clamp(pixels / self.scrollable_height * len(self.final_formatted_text) + 1, 1, len(self.final_formatted_text))

    def scroll_to_nearest_line(self):
        self.scrolled_line = round(self.scrolled_line)

    def set_scroll_height(self, scroll_to: Union[int, float, str, UIMetric]):
        """crops the text component to the place you want to scroll to. This supports
        calculating the y-coord of a specific line or space between two lines (int, float),
        or a specific pixel or percentage (str, UIMetric)

        Args:
            scroll_to (Union[int, float, str, UIMetric]): location of scroll.
        """
        if isinstance(scroll_to, (int, float)):
            scroll_to = clamp(scroll_to, 1, len(self.final_formatted_text))
            self.scrolled_line = scroll_to
        elif isinstance(scroll_to, str):
            self.scrolled_line = self._pixel_height_to_line(UIMetric.parse(scroll_to).to_pixels(self.scrollable_height))
        elif isinstance(scroll_to, UIMetric):
            self.scrolled_line =  self._pixel_height_to_line(scroll_to.to_pixels(self.scrollable_height))
        else:
            self.scrolled_line = 1

    # @overrides UIComponent.to_surf
    def to_surf(self) -> Surface:
        self._recalculate_size()
        if not self.enabled:
            return engine.create_surface(self.size, True)
        # draw the background.
        base_surf = self._create_bg_surf().copy()
        # draw the text
        remaining_chars = self.num_visible_chars
        for line_num, line in enumerate(self.final_formatted_text):
            if remaining_chars <= 0:
                break
            visible_line = line[:remaining_chars]
            remaining_chars -= len(visible_line)
            self.props.font.blit(visible_line, base_surf, pos=(self.padding[0], self.padding[2] + line_num * (self.line_break_size + self.font_height)))

        if self.props.max_lines > 0:
            # crop the text to the max number of lines, to avoid overflow
            scrolled_down_height = (self.scrolled_line - 1) * (self.font_height + self.line_break_size)
            remaining_lines = min(self.props.max_lines, len(self.final_formatted_text) - self.scrolled_line + 1)
            height_of_max_lines = remaining_lines * self.font_height + (remaining_lines - 1) * self.line_break_size
            ret_surf = engine.subsurface(base_surf, (0, scrolled_down_height, self.width, height_of_max_lines))
        else:
            ret_surf = base_surf
        return ret_surf
