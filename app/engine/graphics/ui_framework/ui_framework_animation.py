from __future__ import annotations

from typing import Callable, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from .ui_framework import UIComponent

from pygame import Vector2

def animated(name: str):
    """Decorator that binds an animation to a function call. For example,
    you can associate a "transition_in" animation with the "enable" function of a UIComponent.

    Args:
        name (str): name of animation to be bound
    """
    def animated_inner(func: Callable):
        def wrapper(self: UIComponent, *args, **kwargs):
            if name in self.saved_animations:
                anims = self.saved_animations[name]
                self.queue_animation(anims)
            func(self, *args, **kwargs)
        return wrapper
    return animated_inner

class UIAnimation():
    """An Animation class for the UI.
    
    Usage of this is straightforward. An animation consists of the following:
    
        component [UIComponent]: A UI Component on which to perform the animation.
        
        halt_condition [Callable[[UIComponent], bool]]:
            A function that takes in a UI component and informs us if the animation is finished.
            Defaults to None, which means that it will run before_anim function once, and end
            immediately.
        
        before_anim, do_anim, after_anim [Callable[[UIComponent]]]:
            A series of arbitrary functions that take in a UI Component and alter its properties
            in some way. Namely, these three functions will be called on the provided UI Component
            above.
            
            before_anim is called once, when the animation is begun (via animation.begin())
            do_anim is continuously called.
            after_anim is called once, when the animation ends (via the halt_condition())
    """
    def __init__(self, halt_condition: Callable[[UIComponent], bool] = None, 
                 before_anim: Callable[[UIComponent]] = None, 
                 do_anim: Callable[[UIComponent]] = None, 
                 after_anim: Callable[[UIComponent]] = None):
        self.component: UIComponent = None
        self.before_anim = before_anim
        self.do_anim = do_anim
        self.after_anim = after_anim
        self.should_halt = halt_condition
        
        self.begun = False

    def begin(self):
        if not self.component:
            return
        self.begun = True
        if self.before_anim:
            self.before_anim(self.component)
        
    def update(self) -> bool:
        """Plays the animation.
        If the animation hasn't started, start it.
        If the animation is started, iterate the animation one stage.
        If the animation should stop, finish it and return true.

        Returns:
            bool: Whether the animation has halted.
        """
        if not self.component:
            return False
        if not self.begun:
            self.begin()
            return False
        if self.should_halt is None or self.should_halt(self.component):
            if self.after_anim:
                self.after_anim(self.component)
            # we finished, so we want to reset the animation
            # in case we call it again
            self.reset()
            return True
        else:
            if self.do_anim:
                self.do_anim(self.component)
            return False
    
    def reset(self):
        self.begun = False

    @classmethod
    def translate_anim(cls, start_offset: Vector2, end_offset: Vector2, speed=40, disable_after=False) -> UIAnimation:
        """A shorthand way of creating a translation animation.

        Args:
            start_offset (Vector2): Starting offset
            end_offset (Vector2): Ending offset
            speed (int, optional): Speed of animation, measured in pixels per frame. Defaults to 40.
            disable_after (bool, optional): whether or not to disable the component after the animation halts.
                Useful for transition outs.

        Returns:
            UIAnimation: A UIAnimation that translates the UIComponent from one point to another.
        """
        direction = (end_offset - start_offset).normalize()
        def before_translation(c: UIComponent):
            c.offset = start_offset
        def translate(c: UIComponent):
            c.offset = c.offset + direction * speed
        def should_stop(c: UIComponent) -> bool:
            return (c.offset - end_offset).dot(c.offset - start_offset) >= 0 and not c.offset == start_offset

        def disable(c: UIComponent) -> None:
            c.disable()
        
        if disable_after:
            return cls(halt_condition=should_stop, before_anim=before_translation, do_anim=translate, after_anim=disable)
        else:
            return cls(halt_condition=should_stop, before_anim=before_translation, do_anim=translate)

    @classmethod
    def toggle_anim(cls, enabled: bool=None) -> UIAnimation:
        """A shorthand way of creating an "animation" that does nothing but disable/enable the component.

        Why is this useful? Because Animations are queued; if you want to run a transition and then disable afterwards,
        this is insanely useful since it will wait until the animation adjourns to disable, 
        preventing graphical bugs such as components instantly vanishing on the first frame of an animation.

        Returns:
            UIAnimation: A UIAnimation that disables, enables, or toggles the component. 
                Best used as a way to cap off a chain of queued transition animations.
        """
        if enabled == None:
            def toggle(c: UIComponent):
                if c.enabled:
                    c.disable()
                else:
                    c.enable()
            return cls(before_anim=toggle)
        elif enabled == False:
            def disable(c: UIComponent):
                c.disable()
            return cls(before_anim=disable)
        else:
            def enable(c: UIComponent):
                c.enable()
            return cls(before_anim=enable)

def hybridize_animation(anims: Dict[str, UIAnimation], keyfunction: Callable[[UIComponent], str]) -> UIAnimation:
    """Helper function for "fusing" animations together.

    For example: suppose you want to fuse a transition-out-right and a transition-out-left animation into
    a single animation, "transition_out", for ease of calling. Obviously, transition-out-right will play
    if the component is right-aligned/on the right side of the screen, and vice versa. This function will
    composite those two animations based on a choosing function. You would pass in a dict mapping the string
    "right" to the transition-out-right animation, and "left" to the transition-out-left animation,
    and pass in a function keyfunction that returns "right' if the component is right, and "left" if the component is left.

    Args:
        anims (Dict[str, UIAnimation]): a list of animations with arbitrary keys
        keyfunction (Callable[[UIComponent], str]): a function for determining which key to select at any given time.
            MUST return only keys that are present in the anims Dict.

    Returns:
        UIAnimation: a hybridized UIAnimation.
    """
    def composite_before(c: UIComponent):
        which_anim = keyfunction(c)
        if which_anim in anims and anims[which_anim].before_anim:
            anims[which_anim].before_anim(c)
    def composite_do(c: UIComponent):
        which_anim = keyfunction(c)
        if which_anim in anims and anims[which_anim].do_anim:
            anims[which_anim].do_anim(c)
    def composite_after(c: UIComponent):
        which_anim = keyfunction(c)
        if which_anim in anims and anims[which_anim].after_anim:
            anims[which_anim].after_anim(c)
    def composite_halt(c: UIComponent) -> bool:
        which_anim = keyfunction(c)
        if which_anim in anims:
            if anims[which_anim].should_halt:
                return anims[which_anim].should_halt(c)
        return True
    
    composite_anim = UIAnimation(halt_condition=composite_halt, before_anim=composite_before, do_anim=composite_do, after_anim=composite_after)
    return composite_anim