"""Read-only movement/route trace around two bounded, client-relative clicks.

Requires a manually identified scene and points. Does not edit a save or game
file. It refuses unknown executables and records exact click QPC intervals.
"""
import argparse
import ctypes
import csv
import json
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--select", nargs=2, type=int, required=True)
    parser.add_argument("--first", nargs=2, type=int, required=True)
    parser.add_argument("--second", nargs=2, type=int, required=True)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--seconds", type=float, default=6)
    parser.add_argument("--trace", action="store_true",
                        help="Diagnostic call ordering only; adds debugger overhead")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--virtual-mouse", action="store_true")
    parser.add_argument("--trace-site", action="append", default=[], metavar="NAME=VA",
                        help="Override default write-watch trace sites (1-4 execute sites)")
    parser.add_argument("--already-selected", action="store_true",
                        help="Retain an existing verified selection")
    parser.add_argument("--unit-blob", action="store_true")
    args = parser.parse_args()
    if args.virtual_mouse:
        args.background = True
    if not 0.1 <= args.delay <= 3 or not 2 <= args.seconds <= 15:
        parser.error("Delay 0.1..3 s and duration 2..15 s required")
    checked_file(api(), args.pid)
    helper = ROOT / "modernization/tools/game_window.py"
    telemetry = ROOT / "modernization/tools/telemetry.py"
    def click(option, point):
        before = qpc()
        result = subprocess.run([sys.executable, str(helper), str(args.pid),
                                 option, *map(str, point), "--input-only",
                                 *(["--virtual-mouse"] if args.virtual_mouse else
                                   ["--background"] if args.background else [])],
                                cwd=ROOT, capture_output=True, text=True)
        after = qpc()
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return {"point": point, "qpc_before": before, "qpc_after": after,
                "input_status": json.loads(result.stdout) if args.background else None}
    if not args.already_selected:
        click("--click", args.select)
    sampler = subprocess.Popen([sys.executable, str(telemetry), str(args.pid),
                                "--seconds", str(args.seconds), "--units", "--route-blob",
                                *(["--unit-blob"] if args.unit_blob else [])],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    tracer = None
    trace_path = ROOT / "modernization/logs" / f"repath-trace-{time.time_ns()}.json"
    try:
        if args.trace:
            trace_command = [sys.executable, str(ROOT / "modernization/tools/trace_engine.py"),
                                       str(args.pid), "--seconds", str(args.seconds),
                                       "--output", str(trace_path)]
            if args.trace_site:
                for site in args.trace_site:
                    trace_command.extend(("--site", site))
            else:
                trace_command.extend(("--site", "route_work=0x5128a0",
                                      "--watch-unit0-route"))
            tracer = subprocess.Popen(trace_command, cwd=ROOT,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(0.25)
        first = click("--right-click", args.first)
        time.sleep(args.delay)
        second = click("--right-click", args.second)
        stdout, stderr = sampler.communicate(timeout=args.seconds + 10)
        if sampler.returncode:
            raise RuntimeError(stderr or stdout)
        if tracer is not None:
            trace_stdout, trace_stderr = tracer.communicate(timeout=args.seconds + 10)
            if tracer.returncode:
                raise RuntimeError(trace_stderr or trace_stdout)
    finally:
        if sampler.poll() is None:
            sampler.terminate()
            sampler.communicate(timeout=5)
        if tracer is not None and tracer.poll() is None:
            # Let the bounded tracer finish and restore debug registers.
            tracer.communicate(timeout=args.seconds + 10)
    summary, _ = json.JSONDecoder().raw_decode(stdout)
    unit_csv = Path(summary["unit_candidates"]["csv"])
    rows = [r for r in csv.DictReader(unit_csv.open(newline="")) if int(r["index"]) == 0]
    route_path = Path(summary["unit_candidates"]["route_blob_json"])
    snapshots = json.loads(route_path.read_text(encoding="utf-8"))["samples"]
    result = {"exe_sha256": summary["exe_sha256"],
              "qpc_frequency": summary["qpc_frequency"],
              "selection": args.select, "first_click": first, "second_click": second,
              "unit0_first": summary["unit_candidates"]["first"][0],
              "unit0_last": summary["unit_candidates"]["last"][0],
              "unit0_route_transitions": [r for a, r in zip(rows, rows[1:])
                                          if a["route_value_candidate"] != r["route_value_candidate"]
                                          or a["route_active_candidate"] != r["route_active_candidate"]],
              "route_blob_change_count": len(snapshots),
              "route_blob_json": str(route_path), "unit_csv": str(unit_csv),
              "unit_blob_changes_csv": summary["unit_candidates"].get("unit_blob_changes_csv"),
              "engine_trace": str(trace_path) if args.trace else None,
              "debugger_overhead_present": args.trace,
              "save_modified_by_probe": False,
              "layout_semantics_verified": False}
    output = ROOT / "modernization/logs" / f"repath-{time.time_ns()}.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(output), **result}, indent=2))


if __name__ == "__main__":
    main()
