"""Summarize player-unit route handoff from synchronized read-only probes."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.route_blob import decode


def analyze(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = [r for r in csv.DictReader(Path(report["unit_csv"]).open(newline=""))
            if int(r["index"]) == 0]
    samples = json.loads(Path(report["route_blob_json"]).read_text(encoding="utf-8"))["samples"]
    if not rows or not samples:
        raise ValueError("Missing unit or route samples")
    frequency = report.get("qpc_frequency", 10_000_000)  # legacy local reports
    def qpc(row):
        return int(row["qpc"])
    second = report["second_click"]
    click_start, click_end = second["qpc_before"], second["qpc_after"]
    inactive = [r for r in rows if qpc(r) >= click_start and int(r["route_active_candidate"]) == 0]
    if not inactive:
        raise ValueError("No inactive route phase after second click")
    inactive_start = inactive[0]
    resumed = next((r for r in rows if qpc(r) > qpc(inactive_start)
                    and int(r["route_active_candidate"]) == 1), None)
    if resumed is None:
        raise ValueError("No resumed route in capture window")
    before = next((decode(bytes.fromhex(s["bytes_hex"])) for s in reversed(samples)
                   if int(s["qpc"]) < click_start), None)
    if before is None:
        raise ValueError("No route before second click")
    after = next((route for s in samples if int(s["qpc"]) >= click_start
                  for route in (decode(bytes.fromhex(s["bytes_hex"])),)
                  if route.destination != before.destination), None)
    if after is None:
        raise ValueError("No route destination transition")
    trace = None
    if report.get("engine_trace"):
        data = json.loads(Path(report["engine_trace"]).read_text(encoding="utf-8"))
        if not data["valid_trace"] or data["errors"]:
            raise ValueError("Invalid debugger trace")
        frequency = data["qpc_frequency"]
        unit = data.get("unit0_address")
        events = [e for e in data["events"]
                  if click_start <= e["qpc"] <= qpc(resumed)
                  and (e["site"] in ("unit0_active_write", "unit0_destination_write")
                       or e["site"] == "route_work" and unit is not None
                       and e["registers"]["ecx"] == unit)]
        trace = [{"seconds_after_click_start": round((e["qpc"]-click_start)/frequency, 4),
                  "site": e["site"], "eip": hex(e["eip"])} for e in events]
    return {"source": str(path), "click_interval_seconds":
            round((click_end-click_start)/frequency, 4),
            "route_inactive_to_active_seconds":
            round((qpc(resumed)-qpc(inactive_start))/frequency, 4),
            "first_inactive_after_click_seconds":
            round((qpc(inactive_start)-click_start)/frequency, 4),
            "new_destination": after.destination,
            "old_segment_endpoint": tuple((before.waypoints[-1].x,
                                           before.waypoints[-1].y,
                                           before.waypoints[-1].z)) if before.waypoints else None,
            "new_segment_reaches_destination": after.segment_reaches_destination,
            "unit_before": rows[0], "unit_after": rows[-1],
            "trace_events_during_handoff": trace,
            "debugger_overhead_present": bool(report.get("debugger_overhead_present")),
            "whole_game_stall_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.reports:
        print(json.dumps(analyze(path), indent=2))


if __name__ == "__main__":
    main()
