from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, Tuple, Union

from app.constants import WINHEIGHT, WINWIDTH
from app.engine import engine
from app.utilities.typing import Color4
from PIL import Image
from PIL.Image import LANCZOS

from pygame import Surface

from .premade_animations.animation_templates import toggle_anim
from .ui_framework_animation import UIAnimation, animated
from .ui_framework_layout import (HAlignment, ListLayoutStyle, UILayoutHandler,
                                  UILayoutType, VAlignment)
from .ui_framework_styling import UIMetric

class ResizeMode(Enum):
    MANUAL = 0
    AUTO = 1

class ComponentProperties():
    def __init__(self):
        # used by the parent to position
        self.h_alignment: HAlignment = HAlignment.LEFT  # Horizontal Alignment of Component
        self.v_alignment: VAlignment = VAlignment.TOP   # Vertical Alignment of Component

        self.grid_occupancy: Tuple[int, int] = (1, 1)    # width/height that the component takes up in a grid
        self.grid_coordinate: Tuple[int, int] = (0, 0)   # which grid coordinate the component occupies

        # used by the component to configure itself
        self.bg: Surface = None                         # bg image for the component
        self.bg_color: Color4 = (0, 0, 0, 0)            # (if no bg) - bg fill color for the component
        self.bg_resize_mode: ResizeMode = (             # whether or not the bg will stretch to fit component
            ResizeMode.MANUAL )

        self.layout: UILayoutType = UILayoutType.NONE   # layout type for the component (see ui_framework_layout.py)
        self.list_style: ListLayoutStyle = (            # list layout style for the component, if using UILayoutType.LIST
            ListLayoutStyle.ROW )

        self.resize_mode: ResizeMode = (                # resize mode; AUTO components will dynamically resize themselves,
            ResizeMode.AUTO )                           # whereas MANUAL components will NEVER resize themselves.
                                                        # Probably always use AUTO, since it'll use special logic.

        self.max_width: str = None                      # maximum width str for the component.
                                                        # Useful for dynamic components such as dialog.
        self.max_height: str = None                     # maximum height str for the component.

        self.opacity: float = 1                         # layer opacity for the element.
                                                        # NOTE: changing this from 1 will disable per-pixel alphas
                                                        # for the entire component.


class RootComponent():
    """Dummy component to simulate the top-level window
    """
    def __init__(self):
        self.width: int = WINWIDTH
        self.height: int = WINHEIGHT

class UIComponent():
    def __init__(self, name: str = "", parent: UIComponent = None):
        """A generic UI component. Contains convenient functionality for
        organizing a UI, as well as UI animation support.

        NOTE: If using percentages, all of width, height, offset, and margin
        are stored as percentages of the size of the parent, while
        padding is stored as a percentage of the self's size.

        Margin and Padding are stored as Left, Right, Top, and Bottom.

        self.children are UI component children.
        self.manual_surfaces are manually positioned surfaces, to support more primitive
            and direct control over the UI.
        """
        if not parent:
            self.parent = RootComponent()
        else:
            self.parent = parent

        self.layout_handler = UILayoutHandler(self)

        self.name = name

        self.children: List[UIComponent] = []
        self.manual_surfaces: List[Tuple[Tuple[int, int], Surface]] = []

        self.props: ComponentProperties = ComponentProperties()

        self.isize: List[UIMetric] = [UIMetric.percent(100),
                                      UIMetric.percent(100)]

        self.imargin: List[UIMetric] = [UIMetric.pixels(0),
                                        UIMetric.pixels(0),
                                        UIMetric.pixels(0),
                                        UIMetric.pixels(0)]

        self.ipadding: List[UIMetric] = [UIMetric.pixels(0),
                                         UIMetric.pixels(0),
                                         UIMetric.pixels(0),
                                         UIMetric.pixels(0)]

        # temporary offset (horizontal, vertical) - used for animations
        self.ioffset: List[UIMetric] = [UIMetric.pixels(0),
                                        UIMetric.pixels(0)]

        self.cached_background: Surface = None # contains the rendered background.

        # animation queue
        self.queued_animations: List[UIAnimation] = []
        # saved animations
        self.saved_animations: Dict[str, List[UIAnimation]] = {}

        # secret internal timekeeper, basically never touch this
        self._chronometer: Callable[[], int] = engine.get_time

        self.enabled: bool = True

    def set_chronometer(self, chronometer: Callable[[], int]):
        self._chronometer = chronometer
        for child in self.children:
            child.set_chronometer(chronometer)

    @classmethod
    def create_base_component(cls, win_width=WINWIDTH, win_height=WINHEIGHT) -> UIComponent:
        """Creates a blank component that spans the entire screen; a base component
        to which other components can be attached

        Args:
            win_width (int): pixel width of the window. Defaults to the global setting.
            win_height(int): pixel height of the window. Defaults to the global setting.

        Returns:
            UIComponent: a blank base component
        """
        base = cls()
        base.width = win_width
        base.height = win_height
        return base

    @classmethod
    def from_existing_surf(cls, surf: Surface) -> UIComponent:
        """Creates a sparse UIComponent from an existing surface.

        Args:
            surf (Surface): Surface around which the UIComponent shall be wrapped

        Returns:
            UIComponent: A simple, unconfigured UIComponent consisting of a single surf
        """
        component = cls()
        component.width = surf.get_width()
        component.height = surf.get_height()
        component.set_background(surf)
        return component

    def set_background(self, bg: Union[Surface, Color4]):
        """Set the background of this component to bg_surf.
        If the size doesn't match, it will be rescaled on draw.

        Args:
            bg_surf (Surface): Any surface.
        """
        if isinstance(bg, Surface):
            self.props.bg = bg
        elif isinstance(bg, Color4):
            self.props.bg_color = bg
        # set this to none; the next time we render,
        # the component will regenerate the background.
        # See _create_bg_surf() and to_surf()
        self.cached_background = None

    def set_bg_resize(self, mode: ResizeMode):
        """Changes the resizing policy of the bg for this component.

        Args:
            mode (ResizeMode): a resize policy
        """
        self.props.resize_mode = mode
        # set this to none; the next time we render,
        # the component will regenerate the background.
        # See _create_bg_surf() and to_surf()
        self.cached_background = None

    @property
    def max_width(self) -> int:
        """Returns max width in pixels

        Returns:
            int: max width of component
        """
        return UIMetric.parse(self.props.max_width).to_pixels(self.parent.width)

    @property
    def max_height(self) -> int:
        """return max height in pixels

        Returns:
            int: max height of component
        """
        return UIMetric.parse(self.props.max_height).to_pixels(self.parent.height)

    @property
    def offset(self) -> Tuple[int, int]:
        """returns offset in pixels

        Returns:
            Tuple[int, int]: pixel offset value
        """
        return (self.ioffset[0].to_pixels(self.parent.width),
                self.ioffset[1].to_pixels(self.parent.height))

    @offset.setter
    def offset(self, new_offset: Tuple[str, str]):
        """sets offset

        Args:
            new_offset (Tuple[str, str]): offset str,
                can be in percentages or pixels
        """
        self.ioffset = (UIMetric.parse(new_offset[0]), UIMetric.parse(new_offset[1]))

    @property
    def size(self) -> Tuple[int, int]:
        """Returns the pixel width and height of the component

        Returns:
            Tuple[int, int]: (pixel width, pixel height)
        """
        return (self.width, self.height)

    @size.setter
    def size(self, size_input: Tuple[str, str]):
        """sets the size of the component

        Args:
            size (Tuple[str, str]): a pair of strings (width, height).
                Can be percentages or flat pixels.
        """
        self.isize = [UIMetric.parse(size_input[0]),
                      UIMetric.parse(size_input[1])]

    @property
    def width(self) -> int:
        """width of component in pixels

        Returns:
            int: pixel width
        """
        if self.props.max_width:
            max_width = UIMetric.parse(self.props.max_width).to_pixels(self.parent.width)
            return min(self.isize[0].to_pixels(self.parent.width), max_width)
        else:
            return self.isize[0].to_pixels(self.parent.width)

    @width.setter
    def width(self, width: str):
        """Sets width

        Args:
            width (str): width string. Can be percentage or pixels.
        """
        self.isize[0] = UIMetric.parse(width)

    @property
    def height(self) -> int:
        """height of component in pixels

        Returns:
            int: pixel height
        """
        if self.props.max_height:
            max_height = UIMetric.parse(self.props.max_height).to_pixels(self.parent.height)
            return min(self.isize[1].to_pixels(self.parent.height), max_height)
        else:
            return self.isize[1].to_pixels(self.parent.height)

    @height.setter
    def height(self, height: str):
        """Sets height

        Args:
            height (str): height string. Can be percentage or pixels.
        """
        self.isize[1] = UIMetric.parse(height)

    @property
    def margin(self) -> Tuple[int, int, int, int]:
        """margin of component in pixels

        Returns:
            Tuple[int, int, int, int]: pixel margins (left, right, top, bottom)
        """
        return (self.imargin[0].to_pixels(self.parent.width),
                self.imargin[1].to_pixels(self.parent.width),
                self.imargin[2].to_pixels(self.parent.height),
                self.imargin[3].to_pixels(self.parent.height))

    @margin.setter
    def margin(self, margin: Tuple[str, str, str, str]):
        """sets a margin

        Args:
            margin (Tuple[str, str, str, str]): margin string.
                Can be in pixels or percentages
        """
        self.imargin = [UIMetric.parse(margin[0]),
                        UIMetric.parse(margin[1]),
                        UIMetric.parse(margin[2]),
                        UIMetric.parse(margin[3])]

    @property
    def padding(self) -> Tuple[int, int, int, int]:
        """Padding of component in pixels

        Returns:
            Tuple[int, int, int, int]: pixel padding (left, right, top, bottom)
        """
        return (self.ipadding[0].to_pixels(self.width),
                self.ipadding[1].to_pixels(self.width),
                self.ipadding[2].to_pixels(self.height),
                self.ipadding[3].to_pixels(self.height))

    @padding.setter
    def padding(self, padding: Tuple[str, str, str, str]):
        """sets a padding

        Args:
            padding (Tuple[str, str, str, str]): padding str.
                Can be in pixels or percentages
        """
        self.ipadding = [UIMetric.parse(padding[0]),
                         UIMetric.parse(padding[1]),
                         UIMetric.parse(padding[2]),
                         UIMetric.parse(padding[3])]

    def add_child(self, child: UIComponent):
        """Add a child component to this component.
        NOTE: Order matters, depending on the layout
        set in UIComponent.props.layout.

        Args:
            child (UIComponent): a child UIComponent
        """
        child.parent = self
        child.set_chronometer(self._chronometer)
        self.children.append(child)

    def add_surf(self, surf: Surface, pos: Tuple[int, int]):
        """Add a hard-coded surface to this component.

        Args:
            surf (Surface): A Surface
            pos (Tuple[int, int]): the coordinate position of the top left of surface
        """
        self.manual_surfaces.append((pos, surf))

    def any_children_animating(self) -> bool:
        """Returns whether or not any children are currently in the middle of an animation.
        Useful for deciding whether or not to shut this component down.

        Returns:
            bool: Are any children recursively animating?
        """
        for child in self.children:
            if child.any_children_animating():
                return True
            if len(child.queued_animations) > 0:
                return True
        return False

    @animated('!enter')
    def enter(self):
        """the component enters, i.e. allows it to display.

        Because of the @animated tag, will automatically queue
        the animation named "!enter" if it exists in the UIObject's
        saved animations
        """
        for child in self.children:
            child.enter()
        self.enabled = True

    @animated('!exit')
    def exit(self, is_top_level=True) -> bool:
        """Makes the component exit, i.e. transitions it out

        Because of the @animated tag, will automatically queue
        the animation named "!exit" if it exists in the UIObject's
        saved animations

        This will also recursively exit any children.

        Args:
            is_top_level (bool): Whether or not this is the top level parent.
            If not, then this will not actually disable. This is because if
            you disable a top-level component, then you will never render its children
            anyway; this will avoid graphical bugs such as children vanishing instantly
            before the parent animates out.

        Returns:
            bool: whether or not this is disabled, or is waiting on children to finish animating.
        """
        for child in self.children:
            child.exit(False)
        if not is_top_level:
            return
        if self.any_children_animating() or len(self.queued_animations) > 0:
            # there's an animation playing; wait until afterwards to exit it
            self.queue_animation([toggle_anim(False)], force=True)
        else:
            self.enabled = False

    def enable(self):
        """does the same thing as enter(), except forgoes all animations
        """
        self.enabled = True
        for child in self.children:
            child.enable()

    def disable(self, is_top_level=True):
        """Does the same as exit(), except forgoes all animations.
        """
        self.enabled = False

    def queue_animation(self, animations: List[UIAnimation] = [], names: List[str] = [], force: bool = False):
        """Queues a series of animations for the component. This method can be called with
        arbitrary animations to play, or it can be called with names corresponding to
        an animation saved in its animation dict, or both, with names taking precedence.
        The animations will automatically trigger in the order in which they were queued.

        NOTE: by default, this does not allow queueing when an animation is already playing.

        Args:
            animation (List[UIAnimation], optional): A list of animations to queue. Defaults to [].
            name (List[str], optional): The names of saved animations. Defaults to [].
            force (bool, optional): Whether or not to queue this animation even if other animations are already playing.
            Defaults to False.
        """
        if not force and len(self.queued_animations) > 0:
            return
        for name in names:
            if name in self.saved_animations:
                n_animation = self.saved_animations[name]
                for anim in n_animation:
                    anim.component = self
                    self.queued_animations.append(anim)
        for animation in animations:
            animation.component = self
            self.queued_animations.append(animation)

    def save_animation(self, animation: UIAnimation, name: str):
        """Adds an animation to the UIComponent's animation dict.
        This is useful for adding animations that may be called many times.

        Args:
            animation (UIAnimation): [description]
            name (str): [description]
        """
        if name in self.saved_animations:
            self.saved_animations[name].append(animation)
        else:
            self.saved_animations[name] = [animation]

    def skip_animation(self):
        """clears the animation queue by finishing all of them instantly.
        Useful for skip button implementation.
        """
        for anim in self.queued_animations:
            anim.after_anim()
        self.queued_animations = []

    def update(self):
        """update. used at the moment to advance animations.
        """
        update_time = self._chronometer()
        if len(self.queued_animations) > 0:
            if self.queued_animations[0].update(update_time):
                # the above function call returns True if the animation is finished
                self.queued_animations.pop(0)

    def _create_bg_surf(self) -> Surface:
        """Generates the background surf for this component of identical dimension
        as the component itself. If the background image isn't the same size as the component,
        and we want to rescale, then we will use PIL to rescale. Because rescaling is expensive,
        we'll be making use of limited caching here.

        Returns:
            Surface: A surface of size self.width x self.height, containing a scaled background image.
        """
        if self.props.bg is None:
            surf = engine.create_surface(self.size, True)
            surf.fill(self.props.bg_color)
            return surf
        else:
            if not self.cached_background or not self.cached_background.get_size() == self.size:
                if self.props.bg_resize_mode == ResizeMode.AUTO:
                    bg_raw = engine.surf_to_raw(self.props.bg, 'RGBA')
                    pil_bg = Image.frombytes('RGBA', self.props.bg.get_size(), bg_raw, 'raw')
                    pil_bg = pil_bg.resize(self.size, resample=LANCZOS)
                    bg_scaled = engine.raw_to_surf(pil_bg.tobytes('raw', 'RGBA'), self.size, 'RGBA')
                    self.cached_background = bg_scaled
                else:
                    base = engine.create_surface(self.size, True)
                    base.blit(self.props.bg, (0, 0))
                    self.cached_background = base
            return self.cached_background

    def to_surf(self) -> Surface:
        if not self.enabled:
            return engine.create_surface(self.size, True)
        # draw the background.
        base_surf = self._create_bg_surf().copy()
        # position and then draw all children recursively according to our layout
        for child in self.children:
            child.update()
        for idx, child_pos in enumerate(self.layout_handler.generate_child_positions()):
            child = self.children[idx]
            base_surf.blit(child.to_surf(), child_pos)
        # draw the hard coded surfaces as well.
        for hard_code_child in self.manual_surfaces:
            pos = hard_code_child[0]
            img = hard_code_child[1]
            base_surf.blit(img, (pos[0], pos[0]))

        # handle own opacity
        if self.props.opacity < 1:
            opacity_val = self.props.opacity * 255
            base_surf.set_alpha(opacity_val)
        return base_surf
