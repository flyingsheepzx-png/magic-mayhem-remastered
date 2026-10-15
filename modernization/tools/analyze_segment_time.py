"""Classify complete motion-gate episodes by world-pixel displacement."""
import argparse
import csv
import json
from pathlib import Path
import statistics


def analyze(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(Path(report["unit_csv"]).open(newline="")))
    frequency = report["qpc_frequency"]
    segments = []
    start = None
    for before, after in zip(rows, rows[1:]):
        old = int(before["motion_state_candidate"])
        new = int(after["motion_state_candidate"])
        if old == 0 and new == 1:
            start = before
        elif old == 1 and new == 0 and start is not None:
            x0, y0 = (int(start[key]) for key in ("pixel_x_candidate", "pixel_y_candidate"))
            x1, y1 = (int(after[key]) for key in ("pixel_x_candidate", "pixel_y_candidate"))
            dx, dy = abs(x1-x0), abs(y1-y0)
            kind = ("diagonal" if dx == dy == 32 else
                    "cardinal" if sorted((dx, dy)) == [0, 32] else "other")
            segments.append({"kind": kind, "delta_pixel": [x1-x0, y1-y0],
                             "seconds": (int(after["qpc"])-int(start["qpc"]))/frequency,
                             "start_cell": [int(start[k]) for k in
                                            ("x_candidate", "y_candidate", "z_candidate")]})
            start = None
    grouped = {kind: [x["seconds"] for x in segments if x["kind"] == kind]
               for kind in ("cardinal", "diagonal", "other")}
    return {"source": str(path), "counts": {k: len(v) for k, v in grouped.items()},
            "median_seconds": {k: statistics.median(v) if v else None for k,v in grouped.items()},
            "segments": segments, "may_mix_terrain_and_unit_speed": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reports", nargs="+", type=Path)
    args = ap.parse_args()
    for path in args.reports:
        print(json.dumps(analyze(path), indent=2))


if __name__ == "__main__":
    main()
