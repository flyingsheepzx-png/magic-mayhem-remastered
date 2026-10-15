"""Measure complete-buffer composition and adjacent pixel changes in a trial."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="repath-repeat JSON report")
    parser.add_argument("frames", type=Path, help="render-replay CSV with hashes enabled")
    parser.add_argument("--moving-only", action="store_true",
                        help="Use the first complete unit-0 movement episode after the first order")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    orders = report["orders"]
    if not orders:
        raise SystemExit("Report has no movement orders")
    begin, end = orders[0]["qpc_before"], orders[-1]["qpc_after"]
    if args.moving_only:
        with Path(report["unit_csv"]).open(newline="") as source:
            units = list(csv.DictReader(source))
        click_end = orders[0]["qpc_after"]
        initial = (int(units[0]["pixel_x_candidate"]),
                   int(units[0]["pixel_y_candidate"]))
        moved = next((index for index, row in enumerate(units)
                      if int(row["qpc"]) >= click_end and
                      (int(row["pixel_x_candidate"]),
                       int(row["pixel_y_candidate"])) != initial), None)
        if moved is None:
            raise SystemExit("No unit-0 movement after the first order")
        target = (int(units[-1]["pixel_x_candidate"]),
                  int(units[-1]["pixel_y_candidate"]))
        arrived = next((index for index in range(moved, len(units))
                        if (int(units[index]["pixel_x_candidate"]),
                            int(units[index]["pixel_y_candidate"])) == target), None)
        if arrived is None or arrived == moved:
            raise SystemExit("No complete unit-0 movement episode")
        begin, end = int(units[moved]["qpc"]), int(units[arrived]["qpc"])
    rows = []
    with args.frames.open(newline="") as source:
        for row in csv.reader(source):
            if len(row) < 12 or not row[0].isdigit() or row[1] not in ("native", "replay"):
                continue
            qpc = int(row[0])
            if begin <= qpc <= end:
                rows.append(row)
    if len(rows) < 2 or any(row[4] == "00000000" for row in rows):
        raise SystemExit("Movement window has insufficient hashed frames")
    duration = (int(rows[-1][0]) - int(rows[0][0])) / report["qpc_frequency"]
    if duration <= 0:
        raise SystemExit("Invalid frame timestamps")
    kinds = Counter(row[1] for row in rows)
    repeats = Counter()
    distinct = 0
    for previous, current in zip(rows, rows[1:]):
        if previous[4] == current[4]:
            repeats[f"{previous[1]}_to_{current[1]}"] += 1
        else:
            distinct += 1
    output = {
        "report": str(args.report), "frames": str(args.frames),
        "moving_only": args.moving_only,
        "window_seconds": round(duration, 6),
        "native_compositions": kinds["native"],
        "replay_compositions": kinds["replay"],
        "composition_rate_hz": round(len(rows) / duration, 3),
        "adjacent_distinct_buffers": distinct,
        "adjacent_distinct_rate_hz": round(distinct / duration, 3),
        "adjacent_repeats": dict(repeats),
        "game_time_delta": int(rows[-1][2]) - int(rows[0][2]),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
