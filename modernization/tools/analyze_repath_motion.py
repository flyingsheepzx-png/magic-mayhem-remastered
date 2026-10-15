"""Quantify actual unit-position quiescence near the second route order."""
import argparse
import csv
import json
from pathlib import Path


def analyze(path: Path):
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = [r for r in csv.DictReader(Path(report["unit_csv"]).open(newline=""))
            if int(r["index"]) == 0]
    if not rows or "pixel_x_candidate" not in rows[0]:
        raise ValueError("This probe predates pixel-coordinate sampling")
    frequency = report["qpc_frequency"]
    before = report["second_click"]["qpc_before"] - frequency // 2
    after = report["second_click"]["qpc_after"] + frequency
    rows = [r for r in rows if before <= int(r["qpc"]) <= after]
    changes = []
    last = None
    for row in rows:
        key = tuple(int(row[k]) for k in ("pixel_x_candidate", "pixel_y_candidate"))
        if key != last:
            changes.append((int(row["qpc"]), key,
                            int(row["route_active_candidate"]),
                            int(row["motion_state_candidate"]),
                            int(row["action_state_candidate"])))
            last = key
    gaps = [round((b[0] - a[0])/frequency, 4) for a,b in zip(changes,changes[1:])]
    return {"source": str(path), "position_changes": len(changes),
            "largest_change_gap_seconds": max(gaps) if gaps else None,
            "gaps_seconds": gaps,
            "changes_relative_to_click": [{"seconds": round((q-report["second_click"]["qpc_before"])/frequency,4),
                                            "position": p, "route_active": active,
                                            "motion_state": motion, "action_state": action}
                                           for q,p,active,motion,action in changes],
            "pixel_coordinate_semantics_verified": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reports", nargs="+", type=Path)
    args = ap.parse_args()
    for path in args.reports:
        print(json.dumps(analyze(path), indent=2))


if __name__ == "__main__":
    main()
