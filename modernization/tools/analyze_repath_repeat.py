"""Measure each cliff reroute's route state and fine-position cadence.

This is a diagnostic comparison of candidate engine fields. It does not
declare a visual pause unless fine position itself stops changing.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.route_blob import decode


def summarize(path: Path):
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(Path(report["unit_csv"]).open(newline="")))
    samples = json.loads(Path(report["route_blob_json"]).read_text(encoding="utf-8"))["samples"]
    changes = (list(csv.DictReader(Path(report["unit_blob_changes_csv"]).open(newline="")))
               if report.get("unit_blob_changes_csv") else [])
    frequency = report["qpc_frequency"]
    if "pixel_x_candidate" in rows[0] and any(int(r["pixel_x_candidate"]) for r in rows):
        fine = sorted({int(b["qpc"]) for a, b in zip(rows, rows[1:])
                       if (a["pixel_x_candidate"], a["pixel_y_candidate"]) !=
                          (b["pixel_x_candidate"], b["pixel_y_candidate"])})
    else:
        fine = sorted({int(r["qpc"]) for r in changes if int(r["offset"]) in (0x14, 0x18)})
    results = []
    for i, order in enumerate(report["orders"]):
        start = order["qpc_before"]
        end = (report["orders"][i + 1]["qpc_before"] if i + 1 < len(report["orders"])
               else int(rows[-1]["qpc"]))
        unit = [r for r in rows if start <= int(r["qpc"]) < end]
        route = [(int(s["qpc"]), decode(bytes.fromhex(s["bytes_hex"])).destination)
                 for s in samples if start <= int(s["qpc"]) < end]
        old = next((decode(bytes.fromhex(s["bytes_hex"])).destination
                    for s in reversed(samples) if int(s["qpc"]) < start), None)
        accepted = next(((q, dest) for q, dest in route if dest != old), None)
        inactive = next((r for r in unit if int(r["route_active_candidate"]) == 0), None)
        resumed = (next((r for r in unit if int(r["qpc"]) > int(inactive["qpc"])
                         and int(r["route_active_candidate"]) == 1), None)
                   if inactive else None)
        fine_window = [q for q in fine if start - frequency // 2 <= q < end]
        fine_gaps = [(b-a)/frequency for a,b in zip(fine_window, fine_window[1:])]
        previous_change = next((q for q in reversed(fine) if q < start), None)
        next_change = next((q for q in fine if q >= start), None)
        click_spanning_gap = ((next_change - previous_change) / frequency
                              if previous_change is not None and next_change is not None
                              else None)
        results.append({"order_index": i, "point": order["point"],
                        "destination_accepted": accepted[1] if accepted else None,
                        "accept_seconds_after_click_start":
                        round((accepted[0]-start)/frequency, 4) if accepted else None,
                        "route_inactive_seconds":
                        round((int(resumed["qpc"])-int(inactive["qpc"]))/frequency, 4)
                        if inactive and resumed else None,
                        "fine_position_changes": len(fine_window),
                        "maximum_fine_position_gap_seconds":
                        round(max(fine_gaps), 4) if fine_gaps else None,
                        "fine_position_gap_spanning_click_seconds":
                        round(click_spanning_gap, 4) if click_spanning_gap is not None else None,
                        "start_cell": [int(unit[0][k]) for k in
                                       ("x_candidate", "y_candidate", "z_candidate")] if unit else None,
                        "end_cell": [int(unit[-1][k]) for k in
                                     ("x_candidate", "y_candidate", "z_candidate")] if unit else None})
    return {"source": str(path), "order_count": len(results), "results": results,
            "fine_position_fields_verified": False,
            "visual_stall_verified": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reports", nargs="+", type=Path)
    args = ap.parse_args()
    for path in args.reports:
        print(json.dumps(summarize(path), indent=2))


if __name__ == "__main__":
    main()
