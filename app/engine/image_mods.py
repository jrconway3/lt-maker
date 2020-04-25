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

def change_color(image, color):
    """
    Additively blends a color with the image
    """
    image = engine.copy_surface(image)
    for idx, band in enumerate(color):
        blend_mode = engine.BLEND_RGB_ADD
        if band < 0:
            blend_mode = engine.BLEND_RGB_SUB
            band = -band
        if idx == 0:
            new_color = (band, 0, 0)
        elif idx == 1:
            new_color = (0, band, 0)
        else:
            new_color = (0, 0, band)
        engine.fill(image, new_color, None, blend_mode)
    return image