"""Check that the isolated 1120x840 battle trial adds map pixels at native scale."""

import argparse
from pathlib import Path
import json

from PIL import Image, ImageChops


def image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        return opened.convert("RGB")


def exact_fraction(a: Image.Image, b: Image.Image) -> float:
    assert a.size == b.size
    difference = ImageChops.difference(a, b)
    return sum(pixel == (0, 0, 0) for pixel in difference.get_flattened_data()) / (a.width * a.height)


def dark_fraction(region: Image.Image) -> float:
    return sum(max(pixel) < 8 for pixel in region.get_flattened_data()) / (region.width * region.height)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="800x600 test2 primary-surface screenshot")
    parser.add_argument("expanded", type=Path, help="1120x840 test2 primary-surface screenshot")
    parser.add_argument("--movement-result", type=Path, help="JSON result of --band-move-test")
    args = parser.parse_args()
    old, new = image(args.baseline), image(args.expanded)
    if old.size != (800, 600) or new.size != (1120, 840):
        raise SystemExit(f"Unexpected surface sizes: {old.size}, {new.size}")
    # The extra width/height must be added symmetrically around the original view.
    overlap = new.crop((160, 120, 960, 720))
    terrain = (30, 30, 690, 420)
    terrain_exact = exact_fraction(old.crop(terrain), overlap.crop(terrain))
    new_bands = {
        "left": (0, 0, 160, 840),
        "right": (960, 0, 1120, 840),
        "top": (160, 0, 960, 120),
        "bottom": (160, 720, 960, 840),
    }
    band_dark = {name: round(dark_fraction(new.crop(box)), 4)
                 for name, box in new_bands.items()}
    report = {"area_ratio": round(new.width * new.height / (old.width * old.height), 4),
              "terrain_exact_fraction_after_160_120_translation": round(terrain_exact, 4),
              "new_band_dark_fraction": band_dark}
    if args.movement_result:
        movement = json.loads(args.movement_result.read_text(encoding="utf-8"))
        trial = movement["band_move_test"]
        report["right_band_move"] = {
            "target": trial["target_native"],
            "unit0_before": trial["unit0_before"],
            "unit0_after": trial["unit0_after"],
            "foreground_unchanged": all(entry["foreground"] == movement["foreground_before_input"]
                                        for entry in movement["input"]),
            "startup_did_not_activate": not movement["startup_focus_stolen"],
            "selection_confirmed": trial.get("selection_corner_pixels_confirmed", 0) >= 6,
            "files_restored": movement["restored"] and not movement["changed_saves"],
        }
        if trial["target_native"] != [1000, 420] or trial["unit0_after"][0] <= trial["unit0_before"][0]:
            raise SystemExit("Right-band movement did not move unit 0 toward the target")
        if not all(report["right_band_move"][key] for key in
                   ("foreground_unchanged", "startup_did_not_activate", "selection_confirmed", "files_restored")):
            raise SystemExit("Background isolation or restoration failed")
    print(json.dumps(report, indent=2))
    if terrain_exact < 0.9 or any(value > 0.2 for value in band_dark.values()):
        raise SystemExit("Expanded view did not preserve the original terrain and fill all new bands")


if __name__ == "__main__":
    main()
