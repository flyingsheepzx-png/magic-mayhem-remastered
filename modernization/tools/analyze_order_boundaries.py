"""Compare route activation with 32-pixel cell boundaries after cliff orders."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.route_blob import decode


def nearest(rows, qpc):
    return min(rows, key=lambda row: abs(int(row["qpc"]) - qpc))


def sample(row):
    x, y = (int(row[key]) for key in ("pixel_x_candidate", "pixel_y_candidate"))
    return {"qpc": int(row["qpc"]), "pixel": [x, y],
            "cell": [int(row[key]) for key in ("x_candidate", "y_candidate", "z_candidate")],
            "remainder_32": [x % 32, y % 32],
            "route_active": int(row["route_active_candidate"])}


def analyze(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(Path(report["unit_csv"]).open(newline="")))
    routes = json.loads(Path(report["route_blob_json"]).read_text(encoding="utf-8"))["samples"]
    frequency = report["qpc_frequency"]
    result = []
    for index, order in enumerate(report["orders"]):
        start = order["qpc_before"]
        end = (report["orders"][index + 1]["qpc_before"]
               if index + 1 < len(report["orders"]) else int(rows[-1]["qpc"]))
        earlier = [route for route in routes if route["qpc"] < start]
        old_destination = (decode(bytes.fromhex(earlier[-1]["bytes_hex"])).destination
                           if earlier else None)
        accepted = next((route for route in routes if start <= route["qpc"] < end
                         and decode(bytes.fromhex(route["bytes_hex"])).destination != old_destination),
                        None)
        if accepted is None:
            result.append({"index": index, "accepted": False})
            continue
        q_accept = accepted["qpc"]
        window = [row for row in rows if q_accept <= int(row["qpc"]) < end]
        active = next((row for row in window if int(row["route_active_candidate"]) == 1), None)
        boundary = next((row for row in window
                         if int(row["pixel_x_candidate"]) % 32 == 0
                         and int(row["pixel_y_candidate"]) % 32 == 0), None)
        at_accept = nearest(rows, q_accept)
        result.append({"index": index, "point": order["point"], "accepted": True,
                       "at_accept": sample(at_accept),
                       "first_active": sample(active) if active else None,
                       "first_boundary": sample(boundary) if boundary else None,
                       "activation_delay_seconds":
                       round((int(active["qpc"]) - q_accept) / frequency, 4) if active else None,
                       "boundary_delay_seconds":
                       round((int(boundary["qpc"]) - q_accept) / frequency, 4) if boundary else None})
    return {"source": str(path), "orders": result,
            "order_dispatch_timestamp_exact": False,
            "pixel_fields_are_world_coordinates_candidate": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.reports:
        print(json.dumps(analyze(path), indent=2))


if __name__ == "__main__":
    main()
