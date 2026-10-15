"""Repeated test2 cliff orders with one read-only telemetry window.

Points are fixed client coordinates for the hash-backed fixture. The probe
rejects unexpected initial unit data and reports each click's QPC interval.
"""
import argparse
import ctypes
import csv
import json
from collections import Counter
from pathlib import Path
import subprocess
import sys
import time

from trace_engine import ROOT, api, checked_file


def qpc():
    value = ctypes.c_longlong()
    if not ctypes.WinDLL("kernel32").QueryPerformanceCounter(ctypes.byref(value)):
        raise ctypes.WinError()
    return value.value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pid", type=int)
    ap.add_argument("--cycles", type=int, default=4)
    ap.add_argument("--interval", type=float, default=1.5)
    ap.add_argument("--order-point", nargs=2, type=int, action="append",
                    help="Cycle these client points instead of the default cliff pair")
    ap.add_argument("--warmup-order", nargs=2, type=int)
    ap.add_argument("--warmup-seconds", type=float, default=0)
    ap.add_argument("--unit-blob", action="store_true")
    ap.add_argument("--motion-blob", action="store_true")
    ap.add_argument("--snapshots", action="store_true",
                    help="Request game-surface PNGs after spaced alternate orders")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--watch-unit0-state", action="store_true")
    ap.add_argument("--watch-unit0-render", action="store_true")
    ap.add_argument("--trace-site", action="append", default=[])
    ap.add_argument("--watch-surface-pixel", nargs=2, type=int, metavar=("X", "Y"),
                    help="Watch one byte of the 800x600 game surface")
    ap.add_argument("--watch-memory", type=lambda value: int(value, 0),
                    help="Watch one validated known-process byte address")
    args = ap.parse_args()
    if not 1 <= args.cycles <= 10 or not 0.25 <= args.interval <= 10:
        ap.error("Cycles 1..10 and interval 0.25..10 seconds required")
    points = args.order_point or [(400, 100), (455, 350)]
    if any(not (0 <= x < 800 and 0 <= y < 600) for x, y in points):
        ap.error("Order points must be inside the known 800x600 client")
    checked_file(api(), args.pid)
    helper = ROOT / "modernization/tools/game_window.py"
    telemetry = ROOT / "modernization/tools/telemetry.py"
    def click(button, point):
        before = qpc()
        result = subprocess.run([sys.executable, str(helper), str(args.pid), button,
                                 *map(str, point), "--virtual-mouse", "--input-only"],
                                cwd=ROOT, capture_output=True, text=True)
        after = qpc()
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        ack = json.loads(result.stdout)
        if not ack["private_channel_acknowledged"]:
            raise RuntimeError(f"Private input failed: {ack}")
        return {"point": point, "qpc_before": before, "qpc_after": after}
    initial = subprocess.run([sys.executable, str(telemetry), str(args.pid),
                              "--seconds", "0.1", "--units", "--unit-limit", "1"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
    initial_data, _ = json.JSONDecoder().raw_decode(initial.stdout)
    if initial_data["unit_candidates"]["first"][0][1:4] != [66, 48, 6]:
        raise RuntimeError("test2 initial-unit gate failed")
    select = click("--click", (400, 295))
    warmup = None
    if args.warmup_order:
        if not 0 <= args.warmup_seconds <= 15 or any(not 0 <= c < limit for c,limit in zip(args.warmup_order,(800,600))):
            raise ValueError("Warmup must stay in the known client and last at most 15 seconds")
        warmup = click("--right-click", args.warmup_order)
        time.sleep(args.warmup_seconds)
    duration = args.cycles * 2 * args.interval + 2.0
    sampler = subprocess.Popen([sys.executable, str(telemetry), str(args.pid),
                                "--seconds", str(duration), "--units", "--unit-limit", "1",
                                "--route-blob", *(["--unit-blob"] if args.unit_blob else []),
                                *(["--motion-blob"] if args.motion_blob else [])],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    trace_path = ROOT / "modernization/logs" / f"repath-repeat-trace-{time.time_ns()}.json"
    tracer = None
    if args.trace:
        command = [sys.executable, str(ROOT / "modernization/tools/trace_engine.py"),
                   str(args.pid), "--seconds", str(duration), "--output", str(trace_path)]
        if args.watch_surface_pixel and args.watch_memory is not None:
            raise ValueError("Choose one memory watch")
        if args.watch_memory is not None:
            command.extend(("--watch-memory", hex(args.watch_memory)))
        if args.watch_surface_pixel:
            x, y = args.watch_surface_pixel
            if not (0 <= x < 800 and 0 <= y < 600):
                raise ValueError("Surface pixel outside 800x600")
            surface_log = ROOT / "modernization/logs/surface-calls.csv"
            with surface_log.open(newline="") as source:
                locks = [row for row in csv.reader(source)
                         if len(row) >= 8 and row[1] == "M" and row[5:8] == ["1600", "800", "600"]]
            pointers = Counter(int(row[4], 16) for row in locks)
            if not pointers or pointers.most_common(1)[0][1] < 10:
                raise RuntimeError("No stable 800x600 surface buffer")
            address = pointers.most_common(1)[0][0] + y * 1600 + x * 2
            command.extend(("--watch-memory", hex(address)))
        for site in args.trace_site or (["actor_draw=0x4fa622"]
                                        if args.watch_surface_pixel or args.watch_memory is not None else []):
            command.extend(("--site", site))
        if args.watch_unit0_state:
            command.append("--watch-unit0-state")
        if args.watch_unit0_render:
            command.append("--watch-unit0-render")
        tracer = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
    orders = []
    start = time.monotonic()
    try:
        for index in range(args.cycles * 2):
            planned = start + 0.3 + index * args.interval
            remaining = planned - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            point = points[index % len(points)]
            event = click("--right-click", point)
            event["order_index"] = index
            orders.append(event)
            if args.snapshots and index in (2, 4, 6, 8, 10, 12, 14):
                time.sleep(0.12)
                subprocess.run([sys.executable, str(helper), str(args.pid),
                                "--key", "screenshot", "--input-only", "--virtual-mouse"],
                               cwd=ROOT, capture_output=True, text=True, check=True)
        stdout, stderr = sampler.communicate(timeout=duration + 10)
        if sampler.returncode:
            raise RuntimeError(stderr or stdout)
        if tracer is not None:
            trace_stdout, trace_stderr = tracer.communicate(timeout=duration + 10)
            if tracer.returncode:
                raise RuntimeError(trace_stderr or trace_stdout)
    finally:
        if sampler.poll() is None:
            sampler.terminate()
            sampler.communicate(timeout=5)
        if tracer is not None and tracer.poll() is None:
            tracer.communicate(timeout=duration + 10)
    data, _ = json.JSONDecoder().raw_decode(stdout)
    rows = list(csv.DictReader(Path(data["unit_candidates"]["csv"]).open(newline="")))
    if any(int(r["index"]) != 0 for r in rows):
        raise RuntimeError("Unexpected unit telemetry")
    first, last = data["unit_candidates"]["first"][0], data["unit_candidates"]["last"][0]
    # A zeroed player coordinate or a terminated game invalidates the batch.
    if not all(first[1:4]) or not all(last[1:4]):
        raise RuntimeError("Player unit disappeared; discard this batch and restart")
    result = {"exe_sha256": data["exe_sha256"], "qpc_frequency": data["qpc_frequency"],
              "selection": select, "orders": orders, "unit0_first": first,
              "warmup": warmup, "warmup_seconds": args.warmup_seconds,
              "unit0_last": last, "unit_csv": data["unit_candidates"]["csv"],
              "route_blob_json": data["unit_candidates"]["route_blob_json"],
              "unit_blob_changes_csv": data["unit_candidates"].get("unit_blob_changes_csv"),
              "motion_fields_csv": data["unit_candidates"].get("motion_fields_csv"),
              "engine_trace": str(trace_path) if args.trace else None,
              "debugger_overhead_present": args.trace,
              "whole_game_stall_verified": False, "save_modified_by_probe": False}
    output = ROOT / "modernization/logs" / f"repath-repeat-{time.time_ns()}.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(output), **result}, indent=2))


if __name__ == "__main__":
    main()
