"""Preserve authored chapter portal artwork over the approved map pixels."""
import numpy as np
from PIL import Image

PORTALS = {('Celtic', 9), ('Greek', 13), ('Greek', 14), ('Medieval', 17)}

def composite_portal(base, source):
    assert base.size == (2560, 1440) and source.size == (800, 600)
    rgb = np.array(source.convert('RGB'))
    rgba = np.dstack((rgb, np.where(np.any(rgb != [0, 0, 255], axis=2), 255, 0).astype('uint8')))
    # Pillow resizes RGBA in premultiplied space: keyed blue cannot bleed into
    # the antialiased edge. Original opaque dark pixels remain opaque.
    sprite = Image.fromarray(rgba).resize((1920, 1440), Image.Resampling.LANCZOS)
    overlay = Image.new('RGBA', base.size)
    overlay.paste(sprite, (320, 0))
    result = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    return result, overlay.getchannel('A')
