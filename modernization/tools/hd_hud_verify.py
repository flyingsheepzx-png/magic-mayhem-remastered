"""Verify bottom-right HUD migration against test2 native-surface screenshots."""

import argparse
import json
from pathlib import Path

from PIL import Image


AREAS = {
    "control_limit": (710, 440, 764, 467),
    "portrait": (680, 470, 796, 590),
    "spell_toolbar": (410, 550, 680, 600),
}


def gold(color: tuple[int, int, int]) -> bool:
    return color[0] > 160 and color[1] > 100 and color[0] > color[2] + 60


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_hud", type=Path)
    parser.add_argument("new_hud", type=Path)
    parser.add_argument("--trial", type=Path, help="JSON from the portrait and right-band input trial")
    args = parser.parse_args()
    with Image.open(args.old_hud) as opened:
        old = opened.convert("RGB")
    with Image.open(args.new_hud) as opened:
        new = opened.convert("RGB")
    if old.size != new.size or old.size != (1120, 840):
        raise SystemExit("Expected two 1120x840 native battle screenshots")
    before, after = old.load(), new.load()
    report = {}
    for name, (left, top, right, bottom) in AREAS.items():
        points = [(x, y) for y in range(top, bottom) for x in range(left, right)
                  if gold(before[x, y])]
        matching = sum(sum(abs(before[x, y][channel] - after[x + 320, y + 240][channel])
                           for channel in range(3)) < 20 for x, y in points)
        old_position_gold = sum(gold(after[x, y]) for y in range(top, bottom)
                                for x in range(left, right))
        report[name] = {"old_gold_pixels": len(points),
                        "translated_match_fraction": round(matching / len(points), 4),
                        "gold_pixels_remaining_at_old_position": old_position_gold}
        if len(points) < 100 or matching / len(points) < 0.98 or old_position_gold > 10:
            raise SystemExit(f"HUD area did not move cleanly: {name}: {report[name]}")
    if args.trial:
        result = json.loads(args.trial.read_text(encoding="utf-8"))
        report["interaction"] = {
            "wizard_rect": result["hud_geometry"]["wizard_rect"],
            "portrait_click": [1058, 770] in [entry.get("native") for entry in result["input"]],
            "selection_confirmed": result["band_move_test"]["selection_corner_pixels_confirmed"] >= 6,
            "right_band_move": result["band_move_test"]["unit0_after"][0] >
                               result["band_move_test"]["unit0_before"][0],
            "background": not result["startup_focus_stolen"] and all(
                entry["foreground"] == result["foreground_before_input"] for entry in result["input"]),
            "restored": result["restored"] and not result["changed_saves"],
        }
        if report["interaction"]["wizard_rect"] != [1000, 700, 1115, 840] or not all(
                value for key, value in report["interaction"].items() if key != "wizard_rect"):
            raise SystemExit("Relocated HUD input or rollback verification failed")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
