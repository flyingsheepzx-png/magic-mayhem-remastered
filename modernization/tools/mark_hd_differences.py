"""Mark spatial differences in a baseline-first, full-resolution game capture pair.

Uses the two 2560x1440 game-surface images in comparison.json. The exact
pixel map is retained for audit; a blurred structural map and a coarse-cell
ranking make UI geometry defects visible amid intended Qwen texture changes.
No registration or image resizing is performed, so misalignment stays visible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def boxes(mask: np.ndarray, cell: int, minimum_cells: int = 2):
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    found = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            x0 = x1 = x
            y0 = y1 = y
            count = 0
            while stack:
                cy, cx = stack.pop()
                count += 1
                x0, x1 = min(x0, cx), max(x1, cx)
                y0, y1 = min(y0, cy), max(y1, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if count >= minimum_cells:
                found.append({'box': [x0 * cell, y0 * cell, (x1 + 1) * cell,
                                      (y1 + 1) * cell], 'cells': count})
    return found


def compare(left_path: Path, right_path: Path, output: Path, roi: tuple[int, int, int, int] | None,
            threshold: int, cell: int, blur: float,
            ignore: list[tuple[int, int, int, int]] | None = None):
    with Image.open(left_path) as opened:
        left = opened.convert('RGB')
    with Image.open(right_path) as opened:
        right = opened.convert('RGB')
    if left.size != right.size or left.size != (2560, 1440):
        raise ValueError(f'Expected equal 2560x1440 game surfaces, got {left.size}, {right.size}')
    bounds = (0, 0, 2560, 1440)
    if roi:
        x, y, width, height = roi
        bounds = (x, y, x + width, y + height)
        if x < 0 or y < 0 or width <= 0 or height <= 0 or bounds[2] > 2560 or bounds[3] > 1440:
            raise ValueError('ROI is outside the 2560x1440 surface')
    a = np.asarray(left.crop(bounds), dtype=np.int16)
    b = np.asarray(right.crop(bounds), dtype=np.int16)
    exact = np.max(np.abs(a - b), axis=2).astype(np.uint8)
    smooth_left = np.asarray(left.crop(bounds).filter(ImageFilter.GaussianBlur(blur)), dtype=np.int16)
    smooth_right = np.asarray(right.crop(bounds).filter(ImageFilter.GaussianBlur(blur)), dtype=np.int16)
    structural = np.max(np.abs(smooth_left - smooth_right), axis=2).astype(np.uint8)
    h, w = structural.shape
    ignored = []
    for x, y, width, height in ignore or []:
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 2560 or y + height > 1440:
            raise ValueError('Ignored rectangle is outside the 2560x1440 surface')
        ignored.append([x, y, x + width, y + height])
        x0, y0 = max(0, x - bounds[0]), max(0, y - bounds[1])
        x1, y1 = min(w, x + width - bounds[0]), min(h, y + height - bounds[1])
        if x0 < x1 and y0 < y1:
            exact[y0:y1, x0:x1] = 0
            structural[y0:y1, x0:x1] = 0
    raw_mask = exact >= threshold
    structure_mask = structural >= threshold
    padded_h = ((h + cell - 1) // cell) * cell
    padded_w = ((w + cell - 1) // cell) * cell
    padded = np.zeros((padded_h, padded_w), dtype=np.uint8)
    padded[:h, :w] = structural
    tiles = padded.reshape(padded_h // cell, cell, padded_w // cell, cell)
    tile_mean = tiles.mean(axis=(1, 3))
    tile_fraction = (tiles >= threshold).mean(axis=(1, 3))
    active = (tile_mean >= threshold * .7) & (tile_fraction >= .12)
    regions = boxes(active, cell)
    for region in regions:
        x0, y0, x1, y1 = region['box']
        x1, y1 = min(x1, w), min(y1, h)
        region['box'] = [x0 + bounds[0], y0 + bounds[1], x1 + bounds[0], y1 + bounds[1]]
        crop = structural[y0:y1, x0:x1]
        region['mean_structural_difference'] = round(float(crop.mean()), 2)
        region['fraction_above_threshold'] = round(float((crop >= threshold).mean()), 4)
        region['score'] = round(region['cells'] * region['mean_structural_difference'], 2)
    regions.sort(key=lambda row: row['score'], reverse=True)
    output.mkdir(parents=True, exist_ok=True)
    heat = np.zeros((h, w, 3), dtype=np.uint8)
    heat[:, :, 0] = structural
    heat[:, :, 1] = np.minimum(exact.astype(np.uint16) // 3, 255).astype(np.uint8)
    heat[:, :, 2] = 32
    heat_image = Image.new('RGB', left.size, '#101010')
    heat_image.paste(Image.fromarray(heat), bounds[:2])
    heat_image.save(output / 'structural-heatmap-2560x1440.png')
    pair = Image.new('RGB', (5120, 1440))
    pair.paste(left, (0, 0))
    pair.paste(right, (2560, 0))
    draw = ImageDraw.Draw(pair)
    for index, row in enumerate(regions[:30], 1):
        x0, y0, x1, y1 = row['box']
        for offset in (0, 2560):
            draw.rectangle((x0 + offset, y0, x1 + offset, y1), outline='#ff2828', width=4)
            draw.text((x0 + offset + 3, max(0, y0 - 18)), str(index), fill='#ffff00',
                      stroke_width=2, stroke_fill='#000000')
    if roi:
        for offset in (0, 2560):
            draw.rectangle((bounds[0] + offset, bounds[1], bounds[2] + offset, bounds[3]),
                           outline='#00ffff', width=2)
    for x0, y0, x1, y1 in ignored:
        for offset in (0, 2560):
            draw.rectangle((x0 + offset, y0, x1 + offset, y1), outline='#00aaff', width=2)
    pair.save(output / 'annotated-compare-5120x1440.png')
    report = {'baseline': str(left_path), 'hd': str(right_path), 'surface': [2560, 1440],
              'roi': list(bounds), 'ignored_known_baseline_defects': ignored,
              'threshold': threshold, 'blur_radius': blur, 'cell': cell,
              'exact_fraction_above_threshold': round(float(raw_mask.mean()), 6),
              'structural_fraction_above_threshold': round(float(structure_mask.mean()), 6),
              'exact_mean_difference': round(float(exact.mean()), 3),
              'structural_mean_difference': round(float(structural.mean()), 3),
              'regions': regions}
    (output / 'differences.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('comparison', type=Path, help='baseline-first comparison.json')
    parser.add_argument('page', help='page key in comparison.json')
    parser.add_argument('--roi', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'))
    parser.add_argument('--ignore', nargs=4, type=int, action='append', default=[],
                        metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                        help='exclude a documented baseline defect; shown with a blue outline')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--threshold', type=int, default=48)
    parser.add_argument('--cell', type=int, default=16)
    parser.add_argument('--blur', type=float, default=3.0)
    args = parser.parse_args()
    if not 1 <= args.threshold <= 255 or not 1 <= args.cell <= 128 or args.blur < 0:
        parser.error('invalid threshold, cell or blur')
    pair = json.loads(args.comparison.read_text())['pairs'][args.page]
    out = args.output or args.comparison.parent / f'diff-{args.page}'
    report = compare(Path(pair['baseline']), Path(pair['hd']), out,
                     tuple(args.roi) if args.roi else None, args.threshold, args.cell, args.blur,
                     [tuple(row) for row in args.ignore])
    print(json.dumps({'output': str(out), 'regions': len(report['regions']),
                      'top_regions': report['regions'][:8]}, indent=2))


if __name__ == '__main__':
    main()
