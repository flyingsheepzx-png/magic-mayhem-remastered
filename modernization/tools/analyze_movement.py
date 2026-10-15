"""Summarize candidate route timings from read-only fixed-fixture telemetry.

These are route-field durations, not verified spell/game-time measurements.
Require a complete inactive -> active -> inactive episode and stable endpoint.
"""
import argparse
import csv
import json
from pathlib import Path


def summarize(path: Path, index: int = 0) -> dict:
    session = json.loads(path.read_text(encoding="utf-8"))
    rows = [row for row in csv.DictReader(Path(session["unit_candidates"]["csv"]).open())
            if int(row["index"]) == index]
    if not rows:
        raise ValueError("Unit is absent from telemetry")
    active = [i for i, row in enumerate(rows) if int(row["route_active_candidate"]) == 1]
    if not active or active[0] == 0 or active[-1] == len(rows) - 1:
        raise ValueError("A complete route episode was not captured")
    if active != list(range(active[0], active[-1] + 1)):
        raise ValueError("Multiple route episodes; timing is ambiguous")
    def coordinates(row):
        return [int(row[key]) for key in ("x_candidate", "y_candidate", "z_candidate")]
    first, last = coordinates(rows[0]), coordinates(rows[-1])
    if first == last:
        raise ValueError("No coordinate displacement was captured")
    if any(coordinates(row) != last for row in rows[active[-1] + 1:]):
        raise ValueError("Endpoint did not remain stable after route completion")
    start = float(rows[active[0]]["seconds"])
    end = float(rows[active[-1] + 1]["seconds"])
    gaps = [float(b["seconds"]) - float(a["seconds"]) for a, b in zip(rows, rows[1:])]
    return {"source": str(path), "logic_setting": session["first_values"]["logic_rate_config"],
            "unit_index": index, "start_coordinates_candidate": first,
            "end_coordinates_candidate": last, "route_active_seconds": end - start,
            "maximum_sample_gap_seconds": max(gaps), "samples": len(rows),
            "gameplay_speed_verified": False, "render_fps_measured": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="+", type=Path)
    parser.add_argument("--unit", type=int, default=0)
    args = parser.parse_args()
    for path in args.sessions:
        print(json.dumps(summarize(path, args.unit)))


if __name__ == "__main__":
    main()
