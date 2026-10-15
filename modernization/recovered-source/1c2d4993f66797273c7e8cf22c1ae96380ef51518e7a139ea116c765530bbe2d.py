"""Plan and build the high-definition asset pack with the local Qwen model.

The pipeline is deliberately simple: one local model, one composite step.

  plan   scans the installed art, decides an exact target size, canvas preset,
         strength and route for every asset, writes the machine readable queue,
         writes the human readable asset list and creates the mirrored output
         directory skeleton.
  run    builds the assets that are ready, one manifest each, fully resumable.
  sheet  builds source versus output review sheets.

No other image model is involved. Geometry, colour and letterforms always come
from a Lanczos resample of the original; Qwen-Image 2.1 contributes only a
high-frequency detail band, gated so that text, icons, borders and deliberate
flat fills keep their exact pixels. See docs/local-model-workbench.md for the
service evidence and tools/qwen_canvas.py for the restoration itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_canvas  # noqa: E402
from spr_assets import decode, read_spr  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

DEFAULT_QUEUE = Path("modernization/assets/hd/hd-queue.json")
DEFAULT_PACK = Path("modernization/assets/hd/pack")
DEFAULT_LIST = Path("modernization/assets/HD_ASSET_LIST.md")

# Conventional containers the engine already reads. Anything else is exported
# as PNG until a re-encode path is proven.
# Every output is PNG, whatever the source container was. JPEG is banned from the
# workflow: a second lossy encode damages colour-key fields, and a key that drifts
# stops being transparent, so a magenta or blue rectangle would show in game. PNG is
# lossless and keeps the keyed region byte for byte. The extension change is an
# engine-side item, recorded in HD_PLAN.md.
OUTPUT_SUFFIX = ".png"
# Categories restored on the 2048 canvas class rather than the cheap 1024 one.
UI_CATEGORIES = {"ui-800x600", "ui-untiered"}
RASTER_SUFFIXES = {".jpg", ".jpeg", ".bmp", ".pcx", ".png", ".tga"}
CONTAINER_SUFFIXES = {".spr", ".ani"}
# Deferred by the user on 2026-09-27: tiny cursors gain nothing from a
# generative pass because the canvas floor forces a 24x scale.
DEFERRED_SUFFIXES = {".cur"}


def round_half_up(value: float) -> int:
    return int(value + 0.5)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_queue(queue: dict, path: Path) -> None:
    """Persist each completed job without exposing a half-written queue."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(queue, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    temporary.replace(path)


def classify(relative: str, size: tuple, ui_height: int, art_scale: float):
    """Return (category, target size, note) for one installed asset, or None."""
    parts = relative.split("/")
    folder = parts[0]
    tier = next((p for p in parts if p in {"800x600", "640x480"}), None)
    ui_factor = ui_height / 600.0
    # Folder identity wins over a resolution-tier directory name: Portraits and
    # Bitmaps keep their own 800x600 subfolders but are in-game art, not UI.
    if folder == "Portraits":
        return "portrait", [round_half_up(size[0] * art_scale), round_half_up(size[1] * art_scale)], "in-game art, 2x"
    if folder == "Bitmaps":
        return "bitmap", [round_half_up(size[0] * art_scale), round_half_up(size[1] * art_scale)], "in-game art, 2x, role review required"
    if folder in {"Realms", "Creatures", "Sprites", "Wizards", "Cursors", "AI"}:
        return "in-game-art", [round_half_up(size[0] * art_scale), round_half_up(size[1] * art_scale)], "in-game art, 2x"
    if tier == "640x480":
        return None  # legacy tier, not queued
    if tier == "800x600":
        return "ui-800x600", [round_half_up(size[0] * ui_factor), round_half_up(size[1] * ui_factor)], "native 4:3 UI surface"
    if folder in {"Interface", "SpeechBox"}:
        return "ui-untiered", [round_half_up(size[0] * ui_factor), round_half_up(size[1] * ui_factor)], "UI stored outside a tier folder"
    return None


def plan_record(root: Path, path: Path, args, skipped: dict) -> dict | None:
    relative = path.relative_to(root).as_posix()
    suffix = path.suffix.lower()
    if suffix in DEFERRED_SUFFIXES:
        skipped["cursor-deferred"] = skipped.get("cursor-deferred", 0) + 1
        return None
    # The whole 640x480 tier is the legacy fallback for the same artwork. Keeping
    # it would give one portrait two different output sizes, so it is excluded
    # unless explicitly asked for.
    if "640x480" in relative.split("/") and not args.include_640480:
        skipped["legacy-640x480-tier"] = skipped.get("legacy-640x480-tier", 0) + 1
        return None
    if suffix in CONTAINER_SUFFIXES:
        record = {
            "source": relative, "source_sha256": sha256_file(path), "source_size": None,
            "mode": None, "format": suffix.lstrip("."), "category": "sprite-container",
            "target_size": None, "output": relative, "route": "container-rebuild",
            "preset": None, "content_scale": None, "strength": 0.6,
            "frame_count": None, "frame_size": None, "status": "pending", "note": "",
        }
        if suffix == ".ani":
            record["route"] = "blocked"
            record["status"] = "blocked-sequence-decode"
            record["note"] = "ANI sequence semantics are not decoded; frames and timing are unverified"
            return record
        try:
            _palette, frames = read_spr(path)
        except Exception as error:  # noqa: BLE001 - recorded, never guessed
            record["route"] = "blocked"
            record["status"] = "blocked-format"
            record["note"] = "unsupported container: %s" % str(error)[:120]
            return record
        usable = [f for f in frames if f["width"] and f["height"]]
        if not usable:
            record["route"] = "blocked"
            record["status"] = "blocked-format"
            record["note"] = "no non-empty frames"
            return record
        record["frame_count"] = len(usable)
        record["frame_size"] = [max(f["width"] for f in usable), max(f["height"] for f in usable)]
        box_x = min(f["offset"][0] for f in usable)
        box_y = min(f["offset"][1] for f in usable)
        record["aligned_box"] = [max(f["offset"][0] + f["width"] for f in usable) - box_x,
                                 max(f["offset"][1] + f["height"] for f in usable) - box_y]
        # Realm terrain containers are tile atlases: independent tiles and scenery
        # objects with no ordering, not an animation. Aligning them to one common
        # box is wrong twice over, because a 64x48 tile would sit in a 126x83 box,
        # which makes sparse sheets that fit only nine frames per canvas and
        # measurably halves the model contribution.
        is_atlas = relative.startswith("Realms/") and relative.endswith("Terrain.spr")
        record["route"] = "atlas" if is_atlas else "sheet"
        record["note"] = ("%d independent tiles and objects restored as tight atlas cells" % len(usable)) \
            if is_atlas else ("%d frames restored as one aligned sheet, then split" % len(usable))
        return record
    if suffix not in RASTER_SUFFIXES:
        return None
    try:
        with Image.open(path) as image:
            size, mode = image.size, image.mode
            fmt = (image.format or suffix.lstrip(".")).lower()
    except Exception as error:  # noqa: BLE001
        return {"source": relative, "source_sha256": sha256_file(path), "source_size": None,
                "mode": None, "format": suffix.lstrip("."), "category": "unreadable",
                "target_size": None, "output": None, "route": "blocked", "preset": None,
                "content_scale": None, "strength": None, "status": "unreadable",
                "note": str(error)[:160]}
    classified = classify(relative, size, args.ui_height, args.art_scale)
    if classified is None:
        return None
    category, target, note = classified
    strength = 1.0 if max(size) >= args.large_threshold else 0.6
    work, padding = qwen_canvas.pad_edge(Image.new("RGB", size), args.max_aspect)
    scale = target[0] / size[0]
    # Canvas tier is per category, not global. Native 800x600 UI art is restored at
    # the 2048 class, which measured +288% edge energy against +87% for the 1024
    # class and is what the user asked for; sequence frames, terrain tiles and
    # other small art stay on the cheaper 1024 class.
    tier = args.ui_preset_max_dim if category in UI_CATEGORIES else args.preset_max_dim
    preset, row = qwen_canvas.choose_preset(work.size, scale, tier)
    output = str(Path(relative).with_suffix(OUTPUT_SUFFIX))
    if suffix != OUTPUT_SUFFIX:
        note += "; PNG output, extension change handled engine side"
    return {
        "source": relative, "source_sha256": sha256_file(path), "source_size": list(size),
        "mode": mode, "format": fmt, "category": category, "target_size": target,
        "output": output, "route": "composite", "preset": list(preset),
        "content_scale": row["scale"], "strength": strength, "preset_tier": tier,
        "edge_padding": padding, "status": "pending", "note": note,
    }


def carry_over(previous: dict, record: dict) -> None:
    """Keep processing state when a re-plan produces an identical record."""
    old = previous.get(record["source"])
    if not old or old.get("source_sha256") != record.get("source_sha256"):
        return
    for key in ("target_size", "output", "preset", "strength", "route"):
        if old.get(key) != record.get(key):
            return
    for key in ("status", "output_sha256", "manager_job_id", "seconds", "error"):
        if key in old:
            record[key] = old[key]


def plan(args) -> None:
    root = args.assets_root.resolve(strict=True)
    previous = {}
    if args.queue.exists():
        try:
            previous = {r["source"]: r for r in json.loads(args.queue.read_text(encoding="utf-8"))["records"]}
        except (OSError, ValueError, KeyError):
            previous = {}
    records = []
    skipped: dict = {}
    started = time.monotonic()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith("modernization/"):
            continue
        record = plan_record(root, path, args, skipped)
        if record is None:
            continue
        carry_over(previous, record)
        records.append(record)
    for record in records:
            record["estimate_seconds"] = estimate_seconds(
            record, record.get("preset_tier") or args.preset_max_dim, args.art_scale)
    queue = {
        "schema": 2,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "assets_root": str(root),
        "ui_native": [round_half_up(800 * args.ui_height / 600), args.ui_height],
        "ui_factor": args.ui_height / 600.0,
        "art_scale": args.art_scale,
        "preset_max_dim": args.preset_max_dim,
        "ui_preset_max_dim": args.ui_preset_max_dim,
        "large_threshold": args.large_threshold,
        "skipped": skipped,
        "records": records,
    }
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    write_queue(queue, args.queue)
    created = create_skeleton(records, args.pack)
    write_list(queue, args.list)
    write_csv(queue, args.list.with_suffix(".csv"))
    counters = {}
    for record in records:
        key = record["category"] + "/" + record["status"]
        counters[key] = counters.get(key, 0) + 1
    print("Queue   :", args.queue)
    print("List    :", args.list)
    print("Pack    :", args.pack, "(%d directories)" % created)
    print("UI      : %dx%d  factor %.2f   art scale %.2f" % (
        queue["ui_native"][0], queue["ui_native"][1], queue["ui_factor"], queue["art_scale"]))
    print("Canvas  : %d px for UI art, %d px for animation, terrain and other small art"
          % (args.ui_preset_max_dim, args.preset_max_dim))
    print("Records : %d in %.1fs" % (len(records), time.monotonic() - started))
    for key in sorted(counters):
        print("   %-40s %d" % (key, counters[key]))
    for key in sorted(skipped):
        print("   skipped %-32s %d" % (key, skipped[key]))


def create_skeleton(records: list, pack: Path) -> int:
    """Create the output tree so the pack mirrors the installed layout."""
    created = 0
    for record in records:
        if record.get("route") == "blocked" or not record.get("output"):
            continue
        if record["category"] == "sprite-container":
            target = pack / record["output"]
        else:
            target = (pack / record["output"]).parent
        if not target.exists():
            created += 1
        target.mkdir(parents=True, exist_ok=True)
    return created


def estimate_seconds(record: dict, tier: int, art_scale: float, gap: int = 4) -> float:
    """Rough GPU seconds for one record, from the job times measured on this machine.

    A 1024-class canvas job takes about 8.7 s. Sheet and atlas records pack several
    frames into one canvas, so their cost is the number of canvases they need.
    """
    if record["route"] == "composite":
        # The 2048 canvas class measures about 50 s per asset against 8.7 s for the
        # 1024 class, so the tier dominates the cost of a conventional image.
        preset = record.get("preset") or []
        return 50.0 if preset and max(preset) > 1024 else 8.7
    if record["route"] not in {"sheet", "atlas"}:
        return 0.0
    if not record.get("frame_count"):
        return 0.0
    cell = record["frame_size"] if record["route"] == "atlas" else record.get("aligned_box")
    if not cell:
        return 0.0
    max_content = max(min(preset) for preset in qwen_canvas.PRESETS if max(preset) <= tier)
    per_row = max(1, int((max_content // art_scale + gap) // (cell[0] + gap)))
    sheets = math.ceil(record["frame_count"] / (per_row * per_row))
    return round(sheets * 8.7, 1)


def write_csv(queue: dict, path: Path) -> None:
    import csv
    fields = ["category", "source", "source_size", "target_size", "preset", "content_scale",
              "strength", "route", "frames", "estimate_seconds", "status", "note"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for r in queue["records"]:
            writer.writerow([
                r["category"], r["source"],
                "%dx%d" % tuple(r["source_size"]) if r.get("source_size") else "",
                "%dx%d" % tuple(r["target_size"]) if r.get("target_size") else "",
                "%dx%d" % tuple(r["preset"]) if r.get("preset") else "",
                r.get("content_scale") or "", r.get("strength") or "", r["route"],
                r.get("frame_count") or "", r.get("estimate_seconds") or "",
                r["status"], r.get("error") or r.get("note") or "",
            ])


def write_list(queue: dict, path: Path) -> None:
    records = queue["records"]
    groups = {}
    for record in records:
        groups.setdefault(record["category"], []).append(record)
    runnable = [r for r in records if r["route"] in {"composite", "sheet", "atlas"}]
    blocked = [r for r in records if r["route"] == "blocked"]
    total_seconds = sum(r.get("estimate_seconds") or 0 for r in runnable)
    total_frames = sum(r.get("frame_count") or 0 for r in runnable)

    def human(seconds: float) -> str:
        if seconds < 90:
            return "%.0f s" % seconds
        if seconds < 5400:
            return "%.0f min" % (seconds / 60.0)
        return "%.1f h" % (seconds / 3600.0)

    lines = []
    add = lines.append
    add("# HD build list")
    add("")
    add("Generated by `python modernization/tools/hd_pipeline.py plan` on %s." % queue["generated"])
    add("This file and the matching CSV are generated; do not edit them by hand.")
    add("")
    add("## Confirmed settings")
    add("")
    add("| Setting | Value |")
    add("| --- | --- |")
    add("| UI target | **%dx%d**, a uniform **%.2fx** of the 800x600 tier, 4:3 |"
        % (queue["ui_native"][0], queue["ui_native"][1], queue["ui_factor"]))
    add("| In-game art | **%.1fx** width and height |" % queue["art_scale"])
    add("| Model | Qwen-Image 2.1 only, through the local Manager workbench |")
    add("| Canvas tier | **%d px** for UI art, **%d px** for animation frames, terrain and other small art |"
        % (queue.get("ui_preset_max_dim", queue["preset_max_dim"]), queue["preset_max_dim"]))
    add("| Composite strength | **1.0** at or above %d px on the longer side, otherwise **0.6** |"
        % queue["large_threshold"])
    add("| Sampling | 12 steps, fixed seed per container, prompt enhancement off |")
    add("")
    add("## Method")
    add("")
    add("Geometry, colour and letterforms always come from a Lanczos resample of the")
    add("original, so nothing is invented where it matters. Qwen-Image 2.1 sees the art")
    add("on a canvas whose proportions match one of its fixed presets, and only the")
    add("high-frequency band of its output is added, gated twice: a **structure gate**")
    add("keeps text strokes, icons, borders and hit targets exact, and a **texture gate**")
    add("keeps deliberate flat fills flat. Coverage always comes from the original alpha,")
    add("so silhouettes are byte-identical.")
    add("")
    add("Route decides how frames share a canvas:")
    add("")
    add("- **composite** - one conventional image per job.")
    add("- **sheet** - an animation container. Frames are aligned to the container box so")
    add("  the motion inside each frame is preserved, then split again.")
    add("- **atlas** - a tile atlas such as Realm terrain, which has no ordering. Each")
    add("  frame gets a tight cell of its own size, which packs 49 frames per canvas")
    add("  instead of 9 and roughly doubles the model contribution.")
    add("")
    add("## Measured gain")
    add("")
    add("Edge energy against a plain Lanczos enlargement of the same source to the same")
    add("target, measured on samples across every category:")
    add("")
    add("| Category | Route | Gain |")
    add("| --- | --- | ---: |")
    add("| Grimoire illustration pages | composite | **4.0x** |")
    add("| UI full screens, parchment and maps | composite | **3.3x** |")
    add("| Realm terrain tiles and scenery objects | atlas | **1.2x** |")
    add("| Portraits and small bitmaps | composite | **1.1x** |")
    add("| Creature animation frames | sheet | **1.04x** |")
    add("")
    add("The method pays off where there is smooth surface to carry texture. Hard-edged")
    add("8-bit pixel art puts nearly all of its signal at edges, exactly where the structure")
    add("gate is designed to do nothing, so those categories move only slightly. Terrain at")
    add("1.2x is the better part of that group and is included; creature animation is the")
    add("weakest and is the one item worth reconsidering before it runs for hours.")
    add("")
    add("## Summary")
    add("")
    add("| Group | Assets | Route | Frames | Est. GPU |")
    add("| --- | ---: | --- | ---: | ---: |")
    for category in sorted(groups):
        items = groups[category]
        routes = sorted({r["route"] for r in items})
        seconds = sum(r.get("estimate_seconds") or 0 for r in items)
        counted = sum(r.get("frame_count") or 0 for r in items)
        add("| %s | %d | %s | %s | %s |" % (
            category, len(items), ", ".join(routes), counted or "-",
            human(seconds) if seconds else "-"))
    add("| **total runnable** | **%d** | | **%d** | **%s** |"
        % (len(runnable), total_frames, human(total_seconds)))
    add("")
    add("Estimates assume one job at a time on the installed RTX 5090 at the measured")
    add("8.7 s per 1024-class canvas. Retries, review and installation are extra.")
    add("")
    if blocked:
        add("## Blocked, with the reason on record")
        add("")
        add("| Source | Kind | Files | Why |")
        add("| --- | ---: | ---: | --- |")
        grouped = {}
        for r in blocked:
            key = r["status"]
            entry = grouped.setdefault(key, {"count": 0, "sample": []})
            entry["count"] += 1
            if len(entry["sample"]) < 3:
                entry["sample"].append(r["source"])
        reasons = {
            "blocked-sequence-decode": "ANI sequence definitions. They hold frame indices and a sprite name, no pixels and no geometry, so they need no restoration and stay valid because frame count and order are preserved. 136 files.",
            "blocked-format": "Legacy SPR version 2 containers. The frame table layout is still undecoded; small early UI sprites, low value. 7 files.",
        }
        for key in sorted(grouped):
            entry = grouped[key]
            add("| %s | %s | %d | %s |" % (", ".join("`%s`" % s for s in entry["sample"]),
                                           key, entry["count"], reasons.get(key, "see queue")))
        add("")
    if queue.get("skipped"):
        reasons = {
            "cursor-deferred": "Tiny cursors gain nothing because the canvas floor forces about 24x, so the model invents instead of restoring. Deferred by the user on 2026-09-27.",
            "legacy-640x480-tier": "The same artwork at the legacy resolution. Re-plan with --include-640480 to add it.",
        }
        add("## Not queued")
        add("")
        add("| Group | Assets | Reason |")
        add("| --- | ---: | --- |")
        for key in sorted(queue["skipped"]):
            add("| %s | %d | %s |" % (key, queue["skipped"][key], reasons.get(key, "not queued")))
        add("")
    for category in sorted(groups):
        items = groups[category]
        add("## %s (%d)" % (category, len(items)))
        add("")
        if category == "sprite-container":
            add("| Source | Frames | Frame box | Route | Est. GPU | Status |")
            add("| --- | ---: | --- | --- | ---: | --- |")
            for r in items:
                add("| `%s` | %s | %s | %s | %s | %s |" % (
                    r["source"], r["frame_count"] or "-",
                    "%dx%d" % tuple(r["frame_size"]) if r["frame_size"] else "-",
                    r["route"], human(r.get("estimate_seconds") or 0), r["status"]))
        else:
            add("| Source | From | To | Canvas | Scale | Strength | Est. GPU | Status |")
            add("| --- | --- | --- | --- | ---: | ---: | ---: | --- |")
            for r in items:
                add("| `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
                    r["source"],
                    "%dx%d" % tuple(r["source_size"]) if r["source_size"] else "-",
                    "%dx%d" % tuple(r["target_size"]) if r["target_size"] else "-",
                    "%dx%d" % tuple(r["preset"]) if r["preset"] else "-",
                    ("%.2f" % r["content_scale"]) if r["content_scale"] else "-",
                    r["strength"], human(r.get("estimate_seconds") or 0), r["status"]))
        add("")
    add("## Output layout")
    add("")
    add("`plan` creates a staging tree with paths derived from the installed game:")
    add("")
    add("```")
    add("modernization/assets/hd/pack/")
    add("  Interface/CharacterScreen/800x600/CharacterScreen.png       <- 1920x1440")
    add("  Portraits/800x600/Aeetes 800x600.png                        <- 160x200")
    add("  Creatures/Brownie.spr/0000.png ... plus sprite.json         <- aligned frames")
    add("  Realms/Celtic/Plains/Terrain.spr/0000.png ... sprite.json   <- per-frame size")
    add("```")
    add("")
    add("- All conventional outputs are PNG, including JPEG, BMP, PCX and TGA sources.")
    add("  Changed extensions require a verified engine loading path.")
    add("- Every asset gets a JSON manifest beside it with the source and output SHA-256")
    add("  and the Manager job id.")
    add("- Sprite containers keep frame index, name, source box, offset and flags in")
    add("  sprite.json, which is what a future SPR re-encode needs.")
    add("")
    add("## Install and rollback")
    add("")
    add("Nothing is installed and the engine has not loaded any generated image. The")
    add("engine-side gate is unchanged: the game must render a %dx%d UI natively and draw"
        % (queue["ui_native"][0], queue["ui_native"][1]))
    add("the doubled art at 2x scale, and the coordinate tables in")
    add("`Interface/MainScreen/screen (MainMenu).cfg` and `Grimoire.cfg` must scale by")
    add("**%.2fx** or hit targets will drift." % queue["ui_factor"])
    add("")
    add("The pack cannot be copied into the game as a replacement: source extensions")
    add("change to PNG and SPR output is a frame directory. First prove an opt-in loader")
    add("or re-encoder and native UI/input transforms on the hash-verified executable.")
    add("Before any installation, back up touched files and verify rollback. Then check")
    add("Chinese text, menu hit targets, colour keys, seams, save/load and media playback.")
    add("")
    add("## Open decision")
    add("")
    add("The **sheet** route aligns animation frames to the container box, which is needed")
    add("to keep the motion inside each frame, but it leaves a lot of empty canvas: the")
    add("Brownie container aligns to 68x67 when its largest frame is 37x57. Terrain showed")
    add("that the same sparsity costs about half the model contribution, so animation")
    add("containers are probably being held back the same way. Moving them to tight cells")
    add("would need the re-encode step to restore the original offsets from sprite.json.")
    add("")
    add("## Reproduce")
    add("")
    add("```powershell")
    add("python modernization/tools/hd_pipeline.py plan")
    add("python modernization/tools/hd_pipeline.py run --category ui-800x600")
    add("python modernization/tools/hd_pipeline.py run --category portrait --category bitmap --category ui-untiered")
    add("python modernization/tools/hd_pipeline.py run --category sprite-container")
    add("python modernization/tools/hd_pipeline.py status")
    add("```")
    add("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def flatten(image: Image.Image) -> Image.Image:
    """Composite an RGBA image onto flat black, which is what the canvas needs."""
    background = Image.new("RGB", image.size, (0, 0, 0))
    background.paste(image, (0, 0), image)
    return background


def build_container(record: dict, root: Path, pack: Path, queue: dict, args) -> dict:
    """Restore a whole sprite as one sheet, then split it back into frames.

    One canvas per frame is not viable: at roughly 7.6 s per frame the installed
    28076 frames would take about 59 hours, and a 37x57 frame would be blown up
    about 24 times, leaving the model nothing to work from. One sheet per sprite
    puts the frames at a sane scale, gives the model consistent material, and is
    about 18 times faster. Measured on Brownie over 16 frames: frame to frame
    flicker rises 0.14 percent, and the artefacts the model invents land in the
    transparent gutters, which the alpha discards.
    """
    palette, frames = read_spr(root / record["source"])
    usable = [f for f in frames if f["width"] and f["height"]]
    min_x = min(f["offset"][0] for f in usable)
    min_y = min(f["offset"][1] for f in usable)
    width = max(f["offset"][0] + f["width"] for f in usable) - min_x
    height = max(f["offset"][1] + f["height"] for f in usable) - min_y
    scale = queue["art_scale"]
    target = (round_half_up(width * scale), round_half_up(height * scale))
    aligned = []
    for frame in usable:
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas.paste(decode(palette, frame), (frame["offset"][0] - min_x, frame["offset"][1] - min_y))
        aligned.append(canvas)

    out_dir = pack / record["output"]
    out_dir.mkdir(parents=True, exist_ok=True)
    gap = args.gap
    # Size the grid so one sheet still reaches the target scale inside the chosen
    # canvas tier. A sheet that overflows the canvas comes back below 1:1, which
    # turns the detail band into upscaled noise instead of texture. Measured on
    # the 430 frame Brownie sheet: a 21 by 21 grid on the 1024 tier returned a
    # content scale of 0.679, so the sheet is split into several smaller ones.
    tier = record.get("preset_tier") or queue["preset_max_dim"]
    max_content = max(min(preset) for preset in qwen_canvas.PRESETS if max(preset) <= tier)
    per_row = max(1, int((max_content // scale + gap) // (width + gap)))
    per_sheet = per_row * per_row
    jobs = []
    frame_records = []
    for start in range(0, len(aligned), per_sheet):
        chunk = aligned[start:start + per_sheet]
        cols = min(per_row, len(chunk))
        rows = math.ceil(len(chunk) / cols)
        sheet_w = cols * width + (cols - 1) * gap
        sheet_h = rows * height + (rows - 1) * gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))
        for i, rgba in enumerate(chunk):
            sheet.paste(flatten(rgba), ((i % cols) * (width + gap), (i // cols) * (height + gap)))
        sheet_target = (round_half_up(sheet_w * scale), round_half_up(sheet_h * scale))
        stem = "%s_%05d" % (record["source"].replace("/", "_").replace(".", "_"), start)
        content, meta = qwen_canvas.restore_content(
            sheet, sheet_target, preset_max_dim=tier, steps=args.steps,
            seed=args.seed, work_dir=pack / "_work", stem=stem)
        jobs.append({"start": start, "frames": len(chunk), "grid": [cols, rows],
                     "preset": meta["preset"], "content_scale": meta["content_scale"],
                     "job_id": meta["manager_job_id"], "seconds": meta["qwen_seconds"]})
        detail = qwen_canvas.detail_band(content, args.detail_blur)
        for i, rgba in enumerate(chunk):
            index = start + i
            x = round((i % cols) * (width + gap) * scale)
            y = round((i // cols) * (height + gap) * scale)
            cell_detail = detail.crop((x, y, x + target[0], y + target[1]))
            native = flatten(rgba)
            base = native.resize(target, Image.Resampling.LANCZOS)
            composite = qwen_canvas.apply_detail(base, cell_detail, record["strength"], native)
            composite.putalpha(rgba.getchannel("A").resize(target, Image.Resampling.LANCZOS))
            name = "%04d.png" % index
            composite.save(out_dir / name)
            source_frame = usable[index]
            frame_records.append({
                "index": source_frame["index"], "file": name, "name": source_frame["name"],
                "source_size": [source_frame["width"], source_frame["height"]],
                "offset": list(source_frame["offset"]), "flags": list(source_frame["flags"]),
                "sha256": sha256_file(out_dir / name),
            })
    sheet_out = {
        "status": "hd-prepared-not-installed",
        "tool": "hd_pipeline.build_container",
        "source": record["source"],
        "source_sha256": record["source_sha256"],
        "scale": scale,
        "frame_size": [width, height],
        "target_frame_size": list(target),
        "frames_written": len(frame_records),
        "complete": len(frame_records) == len(usable),
        "frames_per_sheet": per_sheet,
        "sheets": jobs,
        "gap": gap,
        "strength": record["strength"],
        "steps": args.steps,
        "seed": args.seed,
        "rebuild_note": "Frames keep their index, name, source box, offset and flags. "
                         "Re-encoding into SPR still needs container format evidence.",
        "frames": frame_records,
    }
    (out_dir / "sprite.json").write_text(
        json.dumps(sheet_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sheet_out


def build_atlas(record: dict, root: Path, pack: Path, queue: dict, args) -> dict:
    """Restore a container that is a tile atlas rather than an animation.

    Each frame gets a tight cell of the container maximum frame size and is
    pasted at the cell origin, so a sheet holds as many frames as the canvas
    allows instead of being mostly empty box. The result is cropped back to the
    frame own size, so the engine keeps its per-frame geometry and the offsets
    recorded in sprite.json stay meaningful.
    """
    palette, frames = read_spr(root / record["source"])
    usable = [f for f in frames if f["width"] and f["height"]]
    cell_w = max(f["width"] for f in usable)
    cell_h = max(f["height"] for f in usable)
    scale = queue["art_scale"]
    tier = record.get("preset_tier") or queue["preset_max_dim"]
    max_content = max(min(preset) for preset in qwen_canvas.PRESETS if max(preset) <= tier)
    gap = args.gap
    per_row = max(1, int((max_content // scale + gap) // (cell_w + gap)))
    per_sheet = per_row * per_row
    out_dir = pack / record["output"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cell_target = (round_half_up(cell_w * scale), round_half_up(cell_h * scale))
    jobs = []
    frame_records = []
    starts = list(range(0, len(usable), per_sheet))
    if args.max_sheets:
        starts = starts[:args.max_sheets]
    for start in starts:
        chunk = usable[start:start + per_sheet]
        rows = math.ceil(len(chunk) / per_row)
        sheet_w = per_row * cell_w + (per_row - 1) * gap
        sheet_h = rows * cell_h + (rows - 1) * gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))
        for i, frame in enumerate(chunk):
            sheet.paste(flatten(decode(palette, frame)),
                        ((i % per_row) * (cell_w + gap), (i // per_row) * (cell_h + gap)))
        sheet_target = (round_half_up(sheet_w * scale), round_half_up(sheet_h * scale))
        stem = "%s_%05d" % (record["source"].replace("/", "_").replace(".", "_"), start)
        content, meta = qwen_canvas.restore_content(
            sheet, sheet_target, preset_max_dim=tier, steps=args.steps,
            seed=args.seed, work_dir=pack / "_work", stem=stem)
        jobs.append({"start": start, "frames": len(chunk), "grid": [per_row, rows],
                     "preset": meta["preset"], "content_scale": meta["content_scale"],
                     "job_id": meta["manager_job_id"], "seconds": meta["qwen_seconds"]})
        band = qwen_canvas.detail_band(content, args.detail_blur)
        for i, frame in enumerate(chunk):
            sprite = decode(palette, frame)
            cell_native = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
            cell_native.paste(sprite, (0, 0))
            rgb = flatten(cell_native)
            base = rgb.resize(cell_target, Image.Resampling.LANCZOS)
            x = round((i % per_row) * (cell_w + gap) * scale)
            y = round((i // per_row) * (cell_h + gap) * scale)
            cell = band.crop((x, y, x + cell_target[0], y + cell_target[1]))
            composite = qwen_canvas.apply_detail(base, cell, record["strength"], cell_native)
            composite.putalpha(cell_native.getchannel("A").resize(cell_target,
                                                                Image.Resampling.LANCZOS))
            target = (round_half_up(frame["width"] * scale), round_half_up(frame["height"] * scale))
            composite = composite.crop((0, 0, target[0], target[1]))
            name = "%04d.png" % (start + i)
            composite.save(out_dir / name)
            frame_records.append({
                "index": frame["index"], "file": name, "name": frame["name"],
                "source_size": [frame["width"], frame["height"]],
                "target_size": list(target),
                "offset": list(frame["offset"]), "flags": list(frame["flags"]),
                "sha256": sha256_file(out_dir / name),
            })
    atlas_out = {
        "status": "hd-prepared-not-installed",
        "tool": "hd_pipeline.build_atlas",
        "source": record["source"],
        "source_sha256": record["source_sha256"],
        "route": "atlas",
        "scale": scale,
        "cell_size": [cell_w, cell_h],
        "frames_per_sheet": per_sheet,
        "sheets": jobs,
        "gap": gap,
        "strength": record["strength"],
        "steps": args.steps,
        "seed": args.seed,
        "frames_written": len(frame_records),
        "complete": len(frame_records) == len(usable),
        "rebuild_note": "Frames keep index, name, source box, offset and flags. "
                         "Re-encoding into SPR still needs container format evidence.",
        "frames": frame_records,
    }
    (out_dir / "sprite.json").write_text(
        json.dumps(atlas_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return atlas_out


def run(args) -> None:
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    root = Path(queue["assets_root"]).resolve(strict=True)
    selected = [r for r in queue["records"] if r["route"] in {"composite", "sheet", "atlas"}]
    if args.category:
        selected = [r for r in selected if r["category"] in args.category]
    if args.route:
        selected = [r for r in selected if r["route"] in args.route]
    if args.source:
        selected = [r for r in selected
                if any(token.lower() in r["source"].lower() for token in args.source)]
    # The installed sources must still be the ones used to prepare the queue. A
    # completed raster also needs its output and manifest; status alone is not proof.
    for record in selected:
        source = root / record["source"]
        if not source.is_file() or sha256_file(source) != record["source_sha256"]:
            raise RuntimeError("Source changed since plan: " + record["source"])
        if args.only_missing and record["status"] == "done" and record["route"] == "composite":
            output = args.pack / record["output"]
            manifest_path = output.with_suffix(output.suffix + ".json")
            if not output.is_file() or not manifest_path.is_file():
                raise RuntimeError("Completed output or manifest missing: " + record["source"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (sha256_file(output) != record.get("output_sha256")
                    or manifest.get("output_sha256") != record.get("output_sha256")
                    or manifest.get("source_sha256") != record["source_sha256"]):
                raise RuntimeError("Completed output hash mismatch: " + record["source"])
    todo = [r for r in selected if not args.only_missing or r["status"] != "done"]
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        print("Nothing to do")
        return
    print("Building %d assets into %s" % (len(todo), args.pack), flush=True)
    failures = 0
    for index, record in enumerate(todo, 1):
        try:
            if record["route"] == "atlas":
                manifest = build_atlas(record, root, args.pack, queue, args)
            elif record["route"] == "sheet":
                manifest = build_container(record, root, args.pack, queue, args)
            else:
                manifest = qwen_canvas.build_asset(
                    root / record["source"], args.pack / record["output"],
                    tuple(record["target_size"]),
                    preset_max_dim=record.get("preset_tier") or queue["preset_max_dim"],
                    strength=record["strength"], steps=args.steps, seed=args.seed,
                    work_dir=args.pack / "_work")
            # A trial run limited with --max-sheets produces real but incomplete output,
            # so it must stay selectable. Marking it done would silently leave the rest of
            # the container unbuilt on the next full run.
            record["status"] = "partial" if manifest.get("complete") is False else "done"
            record["output_sha256"] = manifest.get("output_sha256")
            record["manager_job_id"] = manifest.get("manager_job_id")
            record["seconds"] = manifest.get("qwen_seconds")
            record["note"] = manifest.get("note") or record.get("note", "")
            record["error"] = None
        except Exception as error:  # noqa: BLE001 - recorded per asset
            record["status"] = "failed"
            record["error"] = ("%s: %s" % (type(error).__name__, error))[:200]
            failures += 1
        print("[%d/%d] %-54s %-8s %5.1fs %s" % (
            index, len(todo), record["source"][-54:], record["status"],
            record.get("seconds") or 0.0, (record.get("error") or "")[:60]), flush=True)
        write_queue(queue, args.queue)
    done = sum(1 for r in queue["records"] if r["status"] == "done")
    print("Finished: %d failed this run; %d done in queue" % (failures, done))
    if failures:
        raise SystemExit(1)


def status(args) -> None:
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    counters = {}
    for record in queue["records"]:
        key = record["category"] + "/" + record["status"]
        counters[key] = counters.get(key, 0) + 1
    print("UI %dx%d factor %.2f | art %.1fx | canvas tier: UI %s, small art %s" % (
        queue["ui_native"][0], queue["ui_native"][1], queue["ui_factor"],
        queue["art_scale"], queue.get("ui_preset_max_dim", "?"), queue["preset_max_dim"]))
    for key in sorted(counters):
        print("   %-42s %d" % (key, counters[key]))


def review(args) -> None:
    """Build contact sheets comparing sources against built outputs.

    Prints the edge-energy gain per category so the batch can be judged without
    opening every file, and writes one PNG per group with the source on the left
    and the built asset on the right.
    """
    import statistics
    from PIL import ImageDraw, ImageFilter, ImageStat
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    root = Path(queue["assets_root"]).resolve(strict=True)
    done = [r for r in queue["records"] if r["status"] == "done" and r.get("output")]
    if args.category:
        done = [r for r in done if r["category"] in args.category]
    if args.route:
        done = [r for r in done if r["route"] in args.route]
    if not done:
        print("Nothing built yet")
        return
    args.review_dir.mkdir(parents=True, exist_ok=True)
    cell = args.cell
    groups = {}
    for record in done:
        groups.setdefault(record["category"], []).append(record)
    print("%-18s %6s %10s %10s" % ("category", "built", "gain median", "gain mean"))
    for category in sorted(groups):
        items = groups[category][:args.limit] if args.limit else groups[category]
        pairs = []
        gains = []
        for record in items:
            source_path = (root / record["source"]) if record["route"] == "composite" \
                else (root / record["source"])
            output_path = args.pack / record["output"]
            if record["route"] != "composite":
                output_path = args.pack / record["output"] / "0000.png"
            try:
                with Image.open(output_path) as handle:
                    after = handle.convert("RGB")
                if record["route"] == "composite":
                    with Image.open(source_path) as handle:
                        before = handle.convert("RGB").resize(after.size, Image.Resampling.LANCZOS)
                else:
                    before = Image.new("RGB", after.size, (24, 24, 24))
            except (OSError, ValueError):
                continue
            if before.size == after.size and max(before.size) >= 8:
                edge = lambda im: ImageStat.Stat(im.convert("L").filter(ImageFilter.FIND_EDGES)).stddev[0]
                base = edge(before)
                if base > 0:
                    gains.append(edge(after) / base)
            pairs.append((record, before, after))
        if gains:
            print("%-18s %6d %10.2f %10.2f" % (category, len(gains),
                                               statistics.median(gains), sum(gains) / len(gains)))
        else:
            print("%-18s %6d %10s %10s" % (category, len(items), "-", "-"))
        if not pairs:
            continue
        columns = args.columns
        rows = (len(pairs) + columns - 1) // columns
        cell_w = cell
        cell_h = round(cell * 3 / 4)
        sheet = Image.new("RGB", (columns * cell_w + (columns + 1) * 6,
                                  rows * (cell_h * 2 + 30) + 10), "#101010")
        draw = ImageDraw.Draw(sheet)
        for i, (record, before, after) in enumerate(pairs):
            col = i % columns
            row = i // columns
            x = 6 + col * (cell_w + 6)
            y = 6 + row * (cell_h * 2 + 30)
            draw.text((x, y), "%s  %s" % (record["source"][-48:], record["target_size"]), fill="#ddd")
            for j, image in enumerate((before, after)):
                thumb = image.copy()
                thumb.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (x, y + 14 + j * (cell_h + 2)))
        path = args.review_dir / ("%s.png" % category)
        sheet.save(path)
        print("   sheet: %s  (%d assets)" % (path, len(pairs)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(target):
        target.add_argument("--assets-root", type=Path, default=Path("."))
        target.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)

    planner = sub.add_parser("plan")
    common(planner)
    planner.add_argument("--list", type=Path, default=DEFAULT_LIST)
    planner.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    planner.add_argument("--ui-height", type=int, default=1440)
    planner.add_argument("--art-scale", type=float, default=2.0)
    planner.add_argument("--preset-max-dim", type=int, default=1024,
                         help="canvas class for sequence frames, terrain and other small art")
    planner.add_argument("--ui-preset-max-dim", type=int, default=2048,
                         help="canvas class for UI art, which the user wants restored at 2K")
    planner.add_argument("--large-threshold", type=int, default=400)
    planner.add_argument("--max-aspect", type=float, default=4.0)
    planner.add_argument("--include-640480", action="store_true",
                         help="also queue the legacy 640x480 tier, which duplicates the 800x600 artwork")
    planner.set_defaults(func=plan)

    runner = sub.add_parser("run")
    common(runner)
    runner.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    runner.add_argument("--category", action="append")
    runner.add_argument("--route", action="append",
                        help="composite, sheet or atlas; repeatable")
    runner.add_argument("--source", action="append", help="substring filter; repeatable")
    runner.add_argument("--limit", type=int)
    runner.add_argument("--steps", type=int, default=12)
    runner.add_argument("--gap", type=int, default=4, help="gutter between frames on a sheet")
    runner.add_argument("--max-sheets", type=int, default=0,
                        help="atlas route only: process just the first N sheets, for a trial")
    runner.add_argument("--detail-blur", type=float, default=1.6)
    runner.add_argument("--seed", type=int, default=260926)
    runner.add_argument("--all", dest="only_missing", action="store_false", default=True)
    runner.set_defaults(func=run)

    report = sub.add_parser("status")
    common(report)
    report.set_defaults(func=status)

    viewer = sub.add_parser("review", help="compare built outputs against their sources")
    common(viewer)
    viewer.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    viewer.add_argument("--review-dir", type=Path,
                        default=Path("modernization/assets/hd/review"))
    viewer.add_argument("--category", action="append")
    viewer.add_argument("--route", action="append")
    viewer.add_argument("--limit", type=int, default=24, help="assets per sheet")
    viewer.add_argument("--columns", type=int, default=6)
    viewer.add_argument("--cell", type=int, default=260)
    viewer.set_defaults(func=review)
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
