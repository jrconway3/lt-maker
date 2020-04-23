from app import utilities
from app.engine import engine

def make_translucent(image, t):
    """
    transparency measured from 0.0 to 1.0, where 0.0 is fully opaque
    and 1.0 is fully transparent
    """

    alpha = 255 - int(255 * t)
    alpha = utilities.clamp(alpha, 0, 255)
    image = engine.copy_surface(image)
    engine.fill(image, (255, 255, 255, alpha), None, engine.BLEND_RGBA_MULT)

    return image

def make_white(image, white):
    """
    whiteness measured from 0.0 to 1.0, where 0.0 is no change to color
    """
    white = int(255 * white)
    white = utilities.clamp(white, 0, 255)
    image = engine.copy_surface(image)
    engine.fill(image, (white, white, white), None, engine.BLEND_RGB_ADD)

    return image
