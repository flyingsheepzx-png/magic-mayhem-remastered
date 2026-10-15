"""Compare first motion in the newly ordered vertical direction.

The fixed alternating `test2` command points make Y direction a useful
read-only proxy. The initial navigation order is omitted from the median.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from statistics import median


def summarize(path: Path):
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(Path(report["unit_csv"]).open(newline="")))
    if any(int(row["index"]) != 0 for row in rows):
        raise ValueError("Expected unit-0-only telemetry")
    changes = [(int(row["qpc"]), int(row["pixel_x_candidate"]),
                int(row["pixel_y_candidate"]))
               for i, row in enumerate(rows)
               if i == 0 or (row["pixel_x_candidate"], row["pixel_y_candidate"]) !=
                            (rows[i - 1]["pixel_x_candidate"],
                             rows[i - 1]["pixel_y_candidate"])]
    jumps = [{"qpc": b[0], "from": a[1:], "to": b[1:],
              "pixels": round(math.hypot(b[1] - a[1], b[2] - a[2]), 2)}
             for a, b in zip(changes, changes[1:])
             if math.hypot(b[1] - a[1], b[2] - a[2]) > 12]
    results = []
    for index, order in enumerate(report["orders"]):
        # Screen Y=100 commands up-cliff motion; Y=350 commands down-cliff.
        sign = -1 if order["point"] == [400, 100] else 1
        start, end = order["qpc_after"], (report["orders"][index + 1]["qpc_before"]
                                              if index + 1 < len(report["orders"])
                                              else changes[-1][0])
        hit = next((b for a, b in zip(changes, changes[1:])
                    if start < b[0] < end and (b[2] - a[2]) * sign > 0), None)
        results.append({"order_index": index,
                        "first_new_direction_seconds":
                        round((hit[0] - start) / report["qpc_frequency"], 4)
                        if hit else None})
    timings = [r["first_new_direction_seconds"] for r in results[1:]
               if r["first_new_direction_seconds"] is not None]
    eligible = max(0, len(results) - 1)
    return {"report": str(path), "order_count": len(results),
            "responsive_orders_after_initial": len(timings),
            "eligible_orders_after_initial": eligible,
            "response_fraction": round(len(timings) / eligible, 4) if eligible else None,
            "median_among_responses_seconds": median(timings) if timings else None,
            "large_position_jumps": jumps, "orders": results,
            "visual_identity_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps([summarize(path) for path in args.reports], indent=2))


if __name__ == "__main__":
    main()
