"""Restore one installed asset with Qwen-Image 2.1 on a padded canvas.

Qwen-Image 2.1 only emits fixed presets (768x1024, 1024x768, 1024x1024,
768x1344, 1344x768, 2048x2048, 2400x1792, 1792x2400, 2752x1536, 1536x2752), so
no preset matches a 4:3 UI surface. This tool fits the asset into a preset-shaped
canvas with flat margins and crops them away again:

1. Choose a preset whose content region can hold the asset at or above the
   requested scale, preferring the smallest usable scale so the model has the
   least room to invent detail.
2. Resize the asset to that content region and centre it on a flat canvas of
   exactly the preset size, so the reference already matches the preset aspect.
3. Let Qwen restore the whole canvas, then crop the content region back out and
   resample it to the exact final target size.

The margins exist only to satisfy the preset. Geometry is carried by the content
region, which is never stretched or cropped, so the restored result lines up with
the original pixel for pixel after scaling.

Three outputs are written per preset:

- the raw model output, for inspection;
- "qwen", the model's own crop resampled to the target, which is a restyle: the
  measured letterform and colour drift make it unusable as a faithful asset;
- "composite", the faithful result. A Lanczos resample of the original supplies
  all geometry, colour and luminance, and only the model's high-frequency detail
  band is added, weighted down wherever the original has structure so text,
  icons and borders keep their exact pixels.

Measured on the main menu at 1920x1440 against a Lanczos baseline: the pure model
output drifts 6.12 in structure and 2.68 in colour, while the composite drifts
0.41 and 0.09 with 5.4x the edge energy. Sampling steps barely change the
composite (12 steps 39.57 edge, 40 steps 38.41), so 12 steps is the default.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

Image.MAX_IMAGE_PIXELS = None

WORKBENCH = "http://127.0.0.1:8790/workbench"
PNG_SIGNATURE = bytes([137, 80, 78, 71, 13, 10, 26, 10])
PRESETS = [
    (768, 1024), (1024, 768), (1024, 1024), (768, 1344), (1344, 768),
    (2048, 2048), (2400, 1792), (1792, 2400), (2752, 1536), (1536, 2752),
]

PROMPT = (
    "Restore and enhance this exact vintage fantasy game artwork at higher resolution. "
    "Reproduce the same composition, framing, silhouette, object placement, text and "
    "lettering, colour and lighting exactly as given. Reconstruct only fine surface "
    "texture: paper fibres, leather grain, stone, metal patina, cloth weave, brush detail. "
    "Do not add, remove or move anything. Do not redraw or restyle any letterform, glyph, "
    "logo, border, button or icon. Do not crop or change the viewpoint. Leave the flat "
    "black margin flat black."
)
NEGATIVE = (
    "text changes, different letters, watermark, signature, new objects, extra decoration, "
    "changed layout, altered geometry, distorted borders, crop, blurry, oversharpened, "
    "halftone dots, jpeg artifacts, colour shift"
)


def round_half_up(value: float) -> int:
    return int(value + 0.5)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def pad_edge(image: Image.Image, max_aspect: float) -> tuple:
    """Edge-replicate a very flat image before it is placed on the canvas.

    A 700x20 status bar has a 35:1 aspect, so its content region inside any
    preset is a sliver surrounded by flat canvas and the model has almost no
    subject to work with. Extending the last row keeps the original pixels at the
    origin, so the result can be cropped straight back.
    """
    width, height = image.size
    pad_w = pad_h = 0
    if width / height > max_aspect:
        pad_h = max(0, round_half_up(width / max_aspect) - height)
    elif height / width > max_aspect:
        pad_w = max(0, round_half_up(height / max_aspect) - width)
    if not pad_w and not pad_h:
        return image, [0, 0]
    padded = Image.new(image.mode, (width + pad_w, height + pad_h))
    padded.paste(image, (0, 0))
    if pad_h:
        padded.paste(image.crop((0, height - 1, width, height)).resize(
            (width, pad_h), Image.Resampling.NEAREST), (0, height))
    if pad_w:
        padded.paste(padded.crop((width - 1, 0, width, height + pad_h)).resize(
            (pad_w, height + pad_h), Image.Resampling.NEAREST), (width, 0))
    return padded, [pad_w, pad_h]


# How hard the structure gate pushes back on an edge, as a multiplier on the
# gradient before it is inverted. Measured over a 49 frame terrain atlas and the
# main menu, a gain of 4 (the first guess) suppressed most of the model output:
# terrain gained 1.03x and the main menu 6.17x. A gain of 1 lets the same
# detail through without touching letterforms: terrain 1.35x, main menu 7.48x,
# character screen 4.80x, with every glyph and every Latin letter intact.
STRUCTURE_EDGE_GAIN = 1.0


def structure_weight(source: Image.Image, target_size: tuple, texture_floor: int = 8,
                     texture_full: int = 24,
                     edge_gain: float = STRUCTURE_EDGE_GAIN) -> Image.Image:
    """255 where generated micro-texture may be added, 0 where it may not.

    Two independent gates, because one is not enough:

    - structure: text strokes, icons, borders and hit-target edges are high
      gradient energy. Generated detail there would smear readable content.
    - texture: a deliberate flat fill, such as the solid blue behind a realm
      silhouette, has no gradient either, so the structure gate alone happily
      textures it and the model invents contour lines inside what should be a
      single colour. Local peak-to-peak range separates the two cases: a flat
      fill measures near zero, a JPEG-compressed flat measures a few levels, and
      parchment or leather measures tens of levels.
    """
    grey = source.convert("L")
    edges = grey.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8))
    flat = edges.point(lambda value: max(0, 255 - value * edge_gain))
    spread = ImageChops.subtract(grey.filter(ImageFilter.MaxFilter(5)),
                                 grey.filter(ImageFilter.MinFilter(5)))
    span = max(1, texture_full - texture_floor)
    gate = spread.point(lambda value: 0 if value <= texture_floor
                        else (255 if value >= texture_full
                              else round(255 * (value - texture_floor) / span)))
    weight = ImageChops.multiply(flat, gate)
    return weight.resize(target_size, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))


def detail_composite(base: Image.Image, restored: Image.Image, strength: float,
                     blur: float, mask_source: Image.Image | None = None) -> Image.Image:
    """Add only the model's high-frequency band, and only where it is allowed.

    The mask is measured on the original asset rather than on the enlarged base,
    so resampling ramps do not inflate the apparent local contrast.
    """
    blurred = restored.filter(ImageFilter.GaussianBlur(blur))
    detail = ImageChops.subtract(restored, blurred, offset=128)
    enhanced = ImageChops.add(base, detail, offset=-128)
    weight = structure_weight(mask_source if mask_source is not None else base,
                              base.size).point(lambda value: round(value * strength))
    return Image.composite(enhanced, base, weight)


def _with_alpha(image: Image.Image, alpha: Image.Image) -> Image.Image:
    out = image.convert("RGBA")
    out.putalpha(alpha.resize(image.size, Image.Resampling.LANCZOS))
    return out


def fit_content(source_size: tuple, preset: tuple) -> tuple:
    """Largest region with the source aspect that fits inside the preset."""
    sw, sh = source_size
    pw, ph = preset
    aspect = sw / sh
    content_w = min(pw, int(round(ph * aspect)))
    content_h = int(round(content_w / aspect))
    if content_h > ph:
        content_h = ph
        content_w = int(round(ph * aspect))
    return content_w, content_h


def preset_table(source_size: tuple, preset_max_dim: int | None = None) -> list:
    """Every allowed preset with the content region it would give this source."""
    rows = []
    for preset in PRESETS:
        if preset_max_dim and max(preset) > preset_max_dim:
            continue
        cw, ch = fit_content(source_size, preset)
        rows.append({"preset": list(preset), "content": [cw, ch],
                     "scale": round(cw / source_size[0], 4),
                     "waste": round(1.0 - (cw * ch) / (preset[0] * preset[1]), 4)})
    return rows


def choose_preset(source_size: tuple, min_scale: float,
                  preset_max_dim: int | None = None) -> tuple:
    """Smallest content scale that reaches min_scale, then the least waste.

    preset_max_dim caps the canvas class. Restoration does not have to run at
    the final pixel size, because the composite only takes a detail band on top
    of a resampled base: a 1024-class canvas costs about a seventh of a
    2048-class one and still carries useful texture, at roughly a third of the
    added edge energy. If no allowed preset reaches min_scale, the nearest
    allowed one is used instead of failing.
    """
    rows = preset_table(source_size, preset_max_dim) or preset_table(source_size)
    usable = [r for r in rows if r["scale"] >= min_scale - 1e-9]
    pool = usable if usable else rows
    key = (lambda r: (r["scale"], r["waste"])) if usable \
        else (lambda r: (abs(r["scale"] - min_scale), r["waste"]))
    best = min(pool, key=key)
    return tuple(best["preset"]), best


def compose(source: Image.Image, preset: tuple) -> tuple:
    cw, ch = fit_content(source.size, preset)
    content = source.convert("RGB").resize((cw, ch), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", preset, (0, 0, 0))
    left = (preset[0] - cw) // 2
    top = (preset[1] - ch) // 2
    canvas.paste(content, (left, top))
    return canvas, (left, top, left + cw, top + ch)


def _post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _get_json(url: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def restore(canvas: Image.Image, size: str, steps: int, seed: int, timeout: int) -> tuple:
    health = _get_json(WORKBENCH + "/api/keyframe2/status")
    if not health.get("engines", {}).get("qwen21", {}).get("ok"):
        raise RuntimeError("Managed Qwen-Image 2.1 is unavailable")
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    payload = {
        "engine": "qwen21",
        "reference_images": ["data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")],
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE,
        "nickname": "Magic and Mayham canvas restoration",
        "quality": "quality",
        "size": size,
        "steps": steps,
        "seed": seed,
        "per_round": 1,
        "official_prompt_enhance": False,
        "transparent": False,
    }
    started = time.monotonic()
    job_id = _post_json(WORKBENCH + "/api/keyframe2/jobs", payload, timeout=60)["job"]["id"]
    print("Manager Qwen job: " + job_id, flush=True)
    deadline = started + timeout
    next_progress = started + 30
    while True:
        job = _get_json(WORKBENCH + "/api/keyframe2/jobs/" + urllib.parse.quote(job_id))["job"]
        # A newly queued job is briefly visible before its request fields are set.
        initializing = job.get("status") in {"queued", "pending", "running"} and not job.get("prompt")
        if not initializing and (job.get("engine") != "qwen21" or job.get("prompt") != PROMPT):
            raise RuntimeError("Qwen job identity does not match this tool")
        if job["status"] in {"completed", "failed", "canceled"}:
            break
        now = time.monotonic()
        if now >= next_progress:
            print("Qwen %s: %s %s; %.0fs elapsed" % (
                job_id, job["status"], job.get("phase_code") or job.get("phase") or "",
                now - started), flush=True)
            next_progress = now + 30
        if time.monotonic() > deadline:
            # Reconcile this exact job before letting the caller select it again.
            # The Manager owns cancellation and keeps uncertain outcomes visible.
            latest = _get_json(WORKBENCH + "/api/keyframe2/jobs/" + urllib.parse.quote(job_id))["job"]
            if latest["status"] == "completed":
                job = latest
                break
            if latest["status"] not in {"failed", "canceled", "cancelled"}:
                _post_json(WORKBENCH + "/api/keyframe2/jobs/" + urllib.parse.quote(job_id) + "/cancel", {}, timeout=60)
            raise TimeoutError("Qwen job timed out: " + job_id)
        time.sleep(2)
    if job["status"] != "completed":
        raise RuntimeError("Qwen job %s: %s" % (job["status"], job.get("phase")))
    candidate = next((seq.get("primary") for seq in job["sequences"] if seq.get("primary")), None)
    if not candidate or not candidate.get("url"):
        raise RuntimeError("Completed Qwen job has no result")
    media_url = urllib.parse.urljoin("http://127.0.0.1:8790", candidate["url"])
    if not media_url.startswith(WORKBENCH + "/api/"):
        raise RuntimeError("Result URL is outside the Manager workbench gateway")
    with urllib.request.urlopen(media_url, timeout=120) as response:
        generated = response.read()
    if not generated.startswith(PNG_SIGNATURE):
        raise RuntimeError("Qwen result is not a PNG")
    return generated, job_id, round(time.monotonic() - started, 2)


def run_one(source_path: Path, args: argparse.Namespace, preset: tuple) -> dict:
    raw = source_path.read_bytes()
    with Image.open(io.BytesIO(raw)) as handle:
        source_rgba = handle.convert("RGBA")
    # Coverage is never generated: a cursor, icon or sprite frame keeps the exact
    # silhouette of the original, so the model cannot invent or eat one.
    alpha = source_rgba.getchannel("A")
    has_alpha = alpha.getextrema()[0] < 255
    source = source_rgba.convert("RGB")
    scale = args.scale
    target = (tuple(int(v) for v in args.target.lower().split("x")) if args.target
              else (round_half_up(source.size[0] * scale), round_half_up(source.size[1] * scale)))
    work, padding = pad_edge(source, args.max_aspect)
    work_target = (round_half_up(work.size[0] * scale), round_half_up(work.size[1] * scale))

    canvas, box = compose(work, preset)
    label = "%dx%d" % preset
    stem = "%s_s%d_%s" % (source_path.stem.replace(" ", "_"), args.steps, label)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    canvas_path = args.out_dir / (stem + "_canvas.png")
    canvas.save(canvas_path)

    generated, job_id, seconds = restore(canvas, label, args.steps, args.seed, args.timeout)
    raw_path = args.out_dir / (stem + "_qwen_raw.png")
    raw_path.write_bytes(generated)
    with Image.open(io.BytesIO(generated)) as handle:
        restored = handle.convert("RGB")
    if restored.size != preset:
        restored = restored.resize(preset, Image.Resampling.LANCZOS)
    content = restored.crop(box).resize(work_target, Image.Resampling.LANCZOS)
    if padding != [0, 0]:
        content = content.crop((0, 0, target[0], target[1]))
    qwen_path = args.out_dir / (stem + "_qwen.png")
    content.save(qwen_path)

    base = source.resize(target, Image.Resampling.LANCZOS)
    base_path = args.out_dir / (stem + "_base.png")
    base.save(base_path)
    composites = []
    for strength in args.detail_strength:
        image = detail_composite(base, content, strength, args.detail_blur, mask_source=source)
        if has_alpha:
            image = _with_alpha(image, alpha)
        path = args.out_dir / ("%s_composite_%.2f.png" % (stem, strength))
        image.save(path)
        composites.append({"strength": strength, "file": path.name,
                           "sha256": sha256_bytes(path.read_bytes())})

    manifest = {
        "status": "experimental-unreviewed-not-installed",
        "tool": "qwen_canvas.py",
        "source": str(source_path),
        "source_sha256": sha256_bytes(raw),
        "source_size": list(source.size),
        "target_size": list(target),
        "preset": list(preset),
        "content_box": list(box),
        "content_scale": round((box[2] - box[0]) / work.size[0], 4),
        "edge_padding": padding,
        "steps": args.steps,
        "seed": args.seed,
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE,
        "official_prompt_enhance": False,
        "manager_job_id": job_id,
        "qwen_seconds": seconds,
        "canvas": canvas_path.name,
        "canvas_sha256": sha256_bytes(canvas_path.read_bytes()),
        "qwen_raw": raw_path.name,
        "qwen_raw_sha256": sha256_bytes(generated),
        "qwen": qwen_path.name,
        "qwen_sha256": sha256_bytes(qwen_path.read_bytes()),
        "base": base_path.name,
        "has_alpha": has_alpha,
        "composites": composites,
        "license_note": "Qwen Research License (non-commercial research/evaluation); "
                        "original game asset rights are separate",
    }
    (args.out_dir / (stem + ".json")).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def detail_band(image: Image.Image, blur: float = 1.6) -> Image.Image:
    """The high-frequency band of an image, offset by 128 for unsigned maths."""
    return ImageChops.subtract(image, image.filter(ImageFilter.GaussianBlur(blur)), offset=128)


def apply_detail(base: Image.Image, detail: Image.Image, strength: float,
                 mask_source: Image.Image) -> Image.Image:
    """Add a prepared detail band to a base wherever the gates allow it."""
    enhanced = ImageChops.add(base, detail, offset=-128)
    weight = structure_weight(mask_source, base.size).point(lambda value: round(value * strength))
    return Image.composite(enhanced, base, weight)


def detect_key_mask(image: Image.Image, tolerance: int = 12, min_fraction: float = 0.04):
    """Find a colour-key background and return (key colour, mask, fraction).

    Old engines made transparency with a key colour rather than an alpha channel:
    pure magenta or pure blue, keyed out at draw time. JPEG sources carry a shifted
    key instead, 251,0,253 for magenta and 0,0,254 for blue, so the test is on border
    pixel values with a tolerance rather than on one exact constant.

    Everything here uses Pillow channel operations, so an 800x600 image costs a few
    milliseconds rather than a Python loop over half a million pixels.
    """
    width, height = image.size
    rgb = image.convert("RGB")
    strips = [rgb.crop((0, 0, width, 1)), rgb.crop((0, height - 1, width, height)),
              rgb.crop((0, 0, 1, height)), rgb.crop((width - 1, 0, width, height))]
    border = Image.new("RGB", (sum(strip.width for strip in strips), 1))
    x = 0
    for strip in strips:
        border.paste(strip.resize((strip.width, 1)), (x, 0))
        x += strip.width
    counts = border.getcolors(maxcolors=1 << 16) or []
    for _, colour in sorted(counts, reverse=True)[:8]:
        red, green, blue = colour
        magenta = red >= 240 and blue >= 240 and green <= 16
        bluish = blue >= 240 and red <= 16 and green <= 16
        if not (magenta or bluish):
            continue
        flat = Image.new("RGB", rgb.size, colour)
        mask = ImageChops.difference(rgb, flat).convert("L").point(
            lambda value: 255 if value <= tolerance else 0)
        fraction = ImageStat.Stat(mask).mean[0] / 255.0
        if fraction >= min_fraction:
            return colour, mask, round(fraction, 4)
    return None, None, 0.0


def protect_key(image: Image.Image, source: Image.Image, mask: Image.Image, ring: int = 2):
    """Put the colour-key region back exactly as it was, plus a thin rim.

    Both parts come from a nearest-neighbour resample of the original, so no value is
    interpolated: the keyed region itself, which must stay one flat colour or the
    engine stops treating it as transparent, and a rim on the sprite side, because
    Lanczos blends the key colour into the art there and would otherwise leave a
    magenta or blue halo around every sprite.
    """
    flat = source.convert("RGB").resize(image.size, Image.Resampling.NEAREST)
    hard = mask.resize(image.size, Image.Resampling.NEAREST)
    restored = Image.composite(flat, image.convert("RGB"), hard)
    rim = ImageChops.subtract(hard.filter(ImageFilter.MaxFilter(2 * ring + 1)), hard)
    return Image.composite(flat, restored, rim)


def grimoire_key_template(source: Image.Image) -> Image.Image:
    """Record the original page's blue and magenta key positions at source size.

    Template values are 0 for art, 1 for the outer blue key and 2 for the inner
    magenta key. Detection reads only the original JPEG, never Qwen output.
    """
    rgb = source.convert("RGB")
    red, green, blue = rgb.split()
    low_red = red.point(lambda value: 255 if value <= 48 else 0)
    low_green = green.point(lambda value: 255 if value <= 32 else 0)
    high_red = red.point(lambda value: 255 if value >= 232 else 0)
    high_blue = blue.point(lambda value: 255 if value >= 232 else 0)
    blue_mask = ImageChops.multiply(ImageChops.multiply(low_red, low_green), high_blue)
    magenta_mask = ImageChops.multiply(ImageChops.multiply(high_red, low_green), high_blue)
    blue_mask = blue_mask.filter(ImageFilter.MaxFilter(3))
    magenta_mask = magenta_mask.filter(ImageFilter.MaxFilter(3))
    template = Image.new("L", rgb.size)
    template.paste(1, mask=blue_mask)
    template.paste(2, mask=magenta_mask)
    return template


def apply_grimoire_key_template(image: Image.Image, template: Image.Image) -> Image.Image:
    """Scale the fixed source template and paint exact key colours over any art."""
    if template.mode != "L":
        raise ValueError("Grimoire key template must be an L image")
    scaled = template.resize(image.size, Image.Resampling.NEAREST)
    blue = scaled.point(lambda value: 255 if value == 1 else 0)
    magenta = scaled.point(lambda value: 255 if value == 2 else 0)
    result = Image.composite(Image.new("RGB", image.size, (0, 0, 255)), image.convert("RGB"), blue)
    return Image.composite(Image.new("RGB", image.size, (255, 0, 255)), result, magenta)


def protect_grimoire_keys(image: Image.Image, source: Image.Image) -> Image.Image:
    """Compatibility wrapper for the source-derived, fixed colour-key template."""
    return apply_grimoire_key_template(image, grimoire_key_template(source))


def restore_content(source: Image.Image, target: tuple, *, preset_max_dim: int | None = None,
                    steps: int = 12, seed: int = 260926, max_aspect: float = 4.0,
                    timeout: int = 2400, work_dir: Path | None = None,
                    stem: str = "asset") -> tuple:
    """Return the model content for one image at the requested target size.

    The image is centred on a preset-shaped canvas, restored, then cropped back
    to the content region and resampled to exactly target. Returns the content
    and the metadata needed for a manifest.
    """
    work, padding = pad_edge(source, max_aspect)
    scale_x = target[0] / source.size[0]
    scale_y = target[1] / source.size[1]
    work_target = (round_half_up(work.size[0] * scale_x), round_half_up(work.size[1] * scale_y))
    preset, row = choose_preset(work.size, scale_x, preset_max_dim)
    canvas, box = compose(work, preset)

    work_dir = work_dir or Path(".")
    work_dir.mkdir(parents=True, exist_ok=True)
    tagged = "%s_%dx%d" % (stem, preset[0], preset[1])
    canvas.save(work_dir / (tagged + "_canvas.png"))
    generated, job_id, seconds = restore(canvas, "%dx%d" % preset, steps, seed, timeout)
    (work_dir / (tagged + "_qwen_raw.png")).write_bytes(generated)
    with Image.open(io.BytesIO(generated)) as handle:
        restored = handle.convert("RGB")
    if restored.size != preset:
        restored = restored.resize(preset, Image.Resampling.LANCZOS)
    content = restored.crop(box).resize(work_target, Image.Resampling.LANCZOS)
    if padding != [0, 0]:
        content = content.crop((0, 0, target[0], target[1]))
    meta = {
        "preset": list(preset), "content_scale": row["scale"], "edge_padding": padding,
        "content_size": [box[2] - box[0], box[3] - box[1]], "canvas_size": list(preset),
        "manager_job_id": job_id, "qwen_seconds": seconds,
    }
    return content, meta


def build_asset(source_path: Path, output_path: Path, target: tuple, *,
                preset_max_dim: int | None = None, strength: float | None = None,
                steps: int = 12, seed: int = 260926, detail_blur: float = 1.6,
                max_aspect: float = 4.0, large_threshold: int = 400,
                timeout: int = 2400, work_dir: Path | None = None) -> dict:
    """Restore one asset and write the composite to output_path.

    The composite is the deliverable: geometry, colour and letterforms come from
    a Lanczos resample of the original, and only the high-frequency detail band
    of the model output is added where the texture and structure gates allow it.
    The raw model output and the canvas are kept beside it for review.
    """
    raw = source_path.read_bytes()
    with Image.open(io.BytesIO(raw)) as handle:
        source_rgba = handle.convert("RGBA")
    alpha = source_rgba.getchannel("A")
    has_alpha = alpha.getextrema()[0] < 255
    source = source_rgba.convert("RGB")
    if strength is None:
        strength = 1.0 if max(source.size) >= large_threshold else 0.6

    # Colour-key transparency: the keyed region must come back byte for byte, or the
    # engine stops keying it out and a magenta or blue rectangle appears in game.
    key_colour, key_mask, key_fraction = (None, None, 0.0)
    if not has_alpha:
        key_colour, key_mask, key_fraction = detect_key_mask(source)

    content, meta = restore_content(source, target, preset_max_dim=preset_max_dim, steps=steps,
                                    seed=seed, max_aspect=max_aspect, timeout=timeout,
                                    work_dir=work_dir or output_path.parent,
                                    stem="%s_s%d" % (source_path.stem.replace(" ", "_"), steps))

    base = source.resize(target, Image.Resampling.LANCZOS)
    grimoire_page = ("Grimoire" in source_path.parts and "800x600" in source_path.parts
                      and source.size == (400, 600))
    if grimoire_page:
        base = protect_grimoire_keys(base, source)
    elif key_mask is not None:
        base = protect_key(base, source, key_mask)
    composite = detail_composite(base, content, strength, detail_blur, mask_source=source)
    if grimoire_page:
        composite = protect_grimoire_keys(composite, source)
    elif key_mask is not None:
        composite = protect_key(composite, source, key_mask)
    if has_alpha:
        composite = _with_alpha(composite, alpha)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    # PNG only. JPEG re-encoding measurably damages a colour-key field, and the key has
    # to stay exact or the engine stops keying it out. PNG is lossless, so the keyed
    # region survives byte for byte.
    composite.save(output_path)

    manifest = {
        "status": "hd-prepared-not-installed",
        "tool": "qwen_canvas.build_asset",
        "source": str(source_path),
        "source_sha256": sha256_bytes(raw),
        "source_size": list(source.size),
        "output": output_path.name,
        "output_sha256": sha256_bytes(output_path.read_bytes()),
        "target_size": list(target),
        "preset": meta["preset"],
        "content_size": meta["content_size"],
        "content_scale": meta["content_scale"],
        "edge_padding": meta["edge_padding"],
        "strength": strength,
        "steps": steps,
        "seed": seed,
        "has_alpha": has_alpha,
        "key_color": list(key_colour) if key_colour else None,
        "key_fraction": key_fraction,
        "key_edge_policy": "grimoire-source-template-v2" if grimoire_page else "legacy-key-rim-v1",
        "manager_job_id": meta["manager_job_id"],
        "qwen_seconds": meta["qwen_seconds"],
        "prompt": PROMPT,
        "official_prompt_enhance": False,
        "license_note": "Qwen Research License (non-commercial research/evaluation); "
                        "original game asset rights are separate",
    }
    output_path.with_suffix(output_path.suffix + ".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--target", default=None,
                        help="final content size; default is the source size times --scale")
    parser.add_argument("--scale", type=float, default=2.4, help="content scale to reach")
    parser.add_argument("--preset", action="append", help="force a preset; repeatable")
    parser.add_argument("--preset-max-dim", type=int, default=None,
                        help="cap the canvas class, for example 1024 for the fast tier")
    parser.add_argument("--max-aspect", type=float, default=4.0,
                        help="edge-replicate sources flatter than this before canvas placement")
    parser.add_argument("--steps", type=int, default=12,
                        help="sampling steps; the composite is insensitive above about 12")
    parser.add_argument("--seed", type=int, default=260926)
    parser.add_argument("--detail-strength", type=float, action="append", default=None,
                        help="composite strength; repeatable. Default is automatic: 1.0 for "
                             "large art, 0.6 below --large-threshold, because a small source "
                             "forces a large canvas scale and the model invents more")
    parser.add_argument("--large-threshold", type=int, default=400,
                        help="source longer side at or above which the default strength is 1.0")
    parser.add_argument("--detail-blur", type=float, default=1.6)
    parser.add_argument("--timeout", type=int, default=2400)
    parser.add_argument("--list-presets", action="store_true")
    args = parser.parse_args()

    source_path = args.source.resolve(strict=True)
    with Image.open(source_path) as handle:
        size = handle.size
    if args.detail_strength is None:
        # Large art tolerates full-strength detail; a small source is blown up
        # many times on the canvas, so the model invents more and a gentler
        # blend keeps it believable.
        auto = 1.0 if max(size) >= args.large_threshold else 0.6
        args.detail_strength = [auto]
        print("auto detail strength %.2f for source %s (threshold %d)"
              % (auto, size, args.large_threshold))
    work, padding = pad_edge(Image.new("RGB", size), args.max_aspect)
    target = (tuple(int(v) for v in args.target.lower().split("x")) if args.target
              else (round_half_up(size[0] * args.scale), round_half_up(size[1] * args.scale)))
    print("source %s %s  target %s  edge padding %s" % (source_path.name, size, target, padding))
    print("%-12s %-14s %7s %7s" % ("preset", "content", "scale", "waste"))
    for row in preset_table(work.size):
        print("%-12s %-14s %7.3f %7.3f" % ("%dx%d" % tuple(row["preset"]),
                                           "%dx%d" % tuple(row["content"]), row["scale"], row["waste"]))
    if args.list_presets:
        return 0

    presets = [tuple(int(v) for v in p.lower().split("x")) for p in args.preset] if args.preset         else [choose_preset(work.size, target[0] / size[0])[0]]
    for preset in presets:
        manifest = run_one(source_path, args, preset)
        print("preset %-10s content %-12s scale %.3f  job %s  %.1fs  composites %s"
              % ("%dx%d" % preset, "%d x %d" % (manifest["content_box"][2] - manifest["content_box"][0],
                                                manifest["content_box"][3] - manifest["content_box"][1]),
                 manifest["content_scale"], manifest["manager_job_id"], manifest["qwen_seconds"],
                 ", ".join("%.2f" % c["strength"] for c in manifest["composites"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
