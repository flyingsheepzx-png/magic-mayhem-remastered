"""Analyze wrapper present attempts and game-surface hashes in a QPC window.

An upload hash is a source-surface identity, not a pixel hash of every output
presentation. The conservative count below assigns the most recent uploaded
hash to each present attempt. It cannot certify shader/output-frame uniqueness.
"""
import argparse
import csv
import ctypes
import json
from pathlib import Path


def analyze(events_path: Path, hashes_path: Path, seconds: float, skip: float) -> dict:
    events = sorted(((int(row["qpc"]), row["event"])
                     for row in csv.DictReader(events_path.open(newline=""))), key=lambda e: e[0])
    hashes = sorted(((int(row["qpc"]), row["hash"], int(row["width"]),
                      int(row["height"]), int(row["bytes_pp"]))
                     for row in csv.DictReader(hashes_path.open(newline=""))), key=lambda e: e[0])
    if not events or not hashes:
        raise ValueError("Both event and hash logs must be nonempty")
    kernel = ctypes.WinDLL("kernel32")
    frequency = ctypes.c_longlong()
    if not kernel.QueryPerformanceFrequency(ctypes.byref(frequency)):
        raise ctypes.WinError()
    start = events[0][0] + int(skip * frequency.value)
    end = start + int(seconds * frequency.value)
    if events[-1][0] < end or hashes[-1][0] < end - frequency.value:
        raise ValueError("Requested interval extends beyond the logs")
    present = [stamp for stamp, kind in events if kind == "P" and start <= stamp < end]
    uploads = [item for item in hashes if start <= item[0] < end]
    assigned = []
    index = 0
    current = None
    for stamp in present:
        while index < len(hashes) and hashes[index][0] <= stamp:
            current = hashes[index][1]
            index += 1
        if current is not None:
            assigned.append(current)
    transitions = sum(a != b for a, b in zip(assigned, assigned[1:]))
    formats = sorted({(w, h, bpp) for _, _, w, h, bpp in uploads})
    return {"seconds": seconds, "skip_seconds": skip,
            "present_attempts": len(present), "surface_uploads_hashed": len(uploads),
            "unique_uploaded_surface_hashes": len({item[1] for item in uploads}),
            "present_attempts_with_known_source_hash": len(assigned),
            "source_hash_transitions_at_present": transitions,
            "source_hash_transition_rate": transitions / seconds,
            "surface_formats": formats, "hash_collision_possible": True,
            "palette_changes_included": False, "output_pixel_frames_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("hashes", type=Path)
    parser.add_argument("--seconds", type=float, default=8)
    parser.add_argument("--skip", type=float, default=0)
    args = parser.parse_args()
    if args.seconds <= 0 or args.skip < 0:
        parser.error("Require positive seconds and nonnegative skip")
    print(json.dumps(analyze(args.events, args.hashes, args.seconds, args.skip), indent=2))


if __name__ == "__main__":
    main()
