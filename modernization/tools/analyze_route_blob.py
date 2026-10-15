"""Decode sparse, read-only route-buffer snapshots from telemetry.py."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.route_blob import decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    data = json.loads(args.file.read_text(encoding="utf-8"))
    records = []
    for sample in data["samples"]:
        try:
            route = decode(bytes.fromhex(sample["bytes_hex"]))
            value = {"seconds": sample["seconds"],
                     "unit_coordinates": sample["coordinates_candidate"],
                     "route_active": sample["route_active_candidate"],
                     "destination": route.destination, "cursor": route.cursor,
                     "count": route.count,
                     "segment_reaches_destination": route.segment_reaches_destination,
                     "waypoints": [(p.x, p.y, p.z) for p in route.waypoints]}
        except ValueError as exc:
            value = {"seconds": sample["seconds"], "invalid_snapshot": str(exc)}
        records.append(value)
    first_by_destination = {}
    last_by_destination = {}
    for record in records:
        if "destination" in record:
            key = tuple(record["destination"])
            first_by_destination.setdefault(key, record)
            last_by_destination[key] = record
    print(json.dumps({"source": str(args.file), "sample_count": len(records),
                      "invalid_snapshots": sum("invalid_snapshot" in r for r in records),
                      "routes": [{"destination": dest,
                                  "first": first_by_destination[dest],
                                  "last": last_by_destination[dest]}
                                 for dest in first_by_destination],
                      "layout_partially_verified": True,
                      "safe_to_write_game_memory": False}, indent=2))


if __name__ == "__main__":
    main()
