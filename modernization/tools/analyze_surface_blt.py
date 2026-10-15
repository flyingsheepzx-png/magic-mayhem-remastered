"""Summarize diagnostic primary-surface writes around repeated cliff orders.

Counts are source-buffer changes at DirectDraw call boundaries, not output FPS.
Full-image hashing adds substantial overhead, so rates are diagnostic only.
"""
import argparse
import collections
import csv
import json
from pathlib import Path


def read_events(path):
    with path.open(newline="") as stream:
        return [(int(row[0]), int(row[1], 16), row[2],
                 int(row[3]) if len(row) > 3 else None)
                for row in csv.reader(stream)]


def summarize(report_path, hash_path, calls_path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    hashes = read_events(hash_path)
    calls = []
    with calls_path.open(newline="") as stream:
        for row in csv.reader(stream):
            if len(row) != 4:
                continue  # Lock memory-layout records are not call counters.
            q, kind, site, primary = row
            calls.append((int(q), kind, int(site, 16), bool(int(primary))))
    frequency = report["qpc_frequency"]
    orders = report["orders"]
    start = report["selection"]["qpc_after"]
    end = orders[-1]["qpc_after"] + 2 * frequency
    sites = collections.defaultdict(lambda: collections.Counter())
    previous = None
    transitions = []
    for q, site, value, thread_id in hashes:
        if previous is not None:
            sites[site]["calls"] += 1
            if value != previous:
                sites[site]["changed"] += 1
                transitions.append(q)
            if thread_id is not None:
                sites[site][f"thread_{thread_id}"] += 1
        previous = value
    windows = []
    for index, order in enumerate(orders):
        q0 = order["qpc_after"]
        q1 = orders[index + 1]["qpc_before"] if index + 1 < len(orders) else end
        selected = [(q, site, value) for q, site, value, _ in hashes if q0 <= q < q1]
        changes = [q for q in transitions if q0 <= q < q1]
        gaps = [(b - a) / frequency for a, b in zip(changes, changes[1:])]
        windows.append({
            "order_index": index, "point": order["point"],
            "seconds": round((q1 - q0) / frequency, 3),
            "blit_hashes": len(selected), "source_changes": len(changes),
            "maximum_change_gap_seconds": round(max(gaps), 4) if gaps else None,
            "sites": dict(collections.Counter(f"{site:08X}" for _, site, _ in selected)),
        })
    return {
        "report": str(report_path), "total_hashes": len(hashes),
        "unique_hashes": len({value for _, _, value, _ in hashes}),
        "call_sites": {f"{site:08X}": dict(counts) for site, counts in sorted(sites.items())},
        "primary_calls": {kind: count for kind, count in collections.Counter(
            kind for _, kind, _, primary in calls if primary).items()},
        "windows": windows,
        "rates_valid_as_fps": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("hashes", type=Path)
    parser.add_argument("calls", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.report, args.hashes, args.calls), indent=2))


if __name__ == "__main__":
    main()
