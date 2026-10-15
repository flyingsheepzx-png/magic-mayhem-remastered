import numpy as np
from PIL import Image
def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def srgb(c):
    return np.where(c < 0.0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** 0.41666 - 0.055)

def render(scale, phase, mask=True):
    h, w = a.shape[:2]
    xx = (np.arange(w * scale) + 0.5) / scale
    yy = (np.arange(h * scale) + 0.5) / scale + phase
    ix = np.floor(xx).astype(int)
    iy = np.floor(yy).astype(int)
    dx = 0.5 - xx % 1
    dy = 0.5 - yy % 1
    pixels = linear(a * 1.08)

    def horz(off, taps, hard):
        result = np.zeros((h * scale, w * scale, 3))
        norm = np.zeros(w * scale)
        for k in range(-taps // 2 + 1, taps // 2 + 1):
            wt = 2 ** (hard * np.abs(dx + k) ** 2)
            result += pixels[np.clip(iy + off, 0, h - 1)[:, None], np.clip(ix + k, 0, w - 1)[None, :]] * wt[None, :, None]
            norm += wt
        return result / norm[None, :, None]
    tri = sum((horz(off, taps, -3) * (2 ** (-8 * np.abs(dy + off) ** 2))[:, None, None] for off, taps in [(-1, 3), (0, 5), (1, 3)]))
    bloom = sum((horz(off, taps, -1.5) * (2 ** (-2 * np.abs(dy + off) ** 2))[:, None, None] for off, taps in [(-2, 5), (-1, 7), (0, 7), (1, 7), (2, 5)]))
    color = tri + bloom * 0.08
    if mask:
        gx, gy = np.meshgrid(np.arange(w * scale) + 0.5, np.arange(h * scale) + 0.5)
        posx = np.floor(gx) + np.floor(gy * 0.5) * 3
        phase_mask = posx * 0.166666666 % 1
        m = np.full(color.shape, 0.55)
        m[:, :, 0][phase_mask < 0.333] = 1.5
        m[:, :, 1][(phase_mask >= 0.333) & (phase_mask < 0.666)] = 1.5
        m[:, :, 2][phase_mask >= 0.666] = 1.5
        color *= m
    return Image.fromarray(np.rint(srgb(color).clip(0, 1) * 255).astype('uint8'))
