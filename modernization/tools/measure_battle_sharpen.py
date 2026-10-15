"""Measure owned game presentation count and CPU use for optional sharpen."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import time

from compare_hd_baseline import CaptureSession, ROOT, sha

FIXTURE_SHA = "56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d"
WRAPPER_SHA = "015a369ee8b8654434b3e745e61befe63346db521f4bb6acc5b3aca1e9e7796d"


def cpu_seconds(session: CaptureSession) -> float:
    fields = [W.FILETIME() for _ in range(4)]
    if not session.k.GetProcessTimes(session.handle, *(ctypes.byref(f) for f in fields)):
        raise ctypes.WinError(ctypes.get_last_error())
    def ticks(f: W.FILETIME) -> int:
        return (f.dwHighDateTime << 32) | f.dwLowDateTime
    return (ticks(fields[2]) + ticks(fields[3])) / 10_000_000


def uploads(session: CaptureSession) -> int:
    value = ctypes.c_size_t()
    if not session.u.SendMessageTimeoutW(session.window(), session.channel, 0x804e,
                                         0, 2, 2000, ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.value


def main() -> None:
    runtime = ROOT / "modernization/playtests/mixed-ui-v4/game-wide169"
    fixture = runtime / "Save/test2.sav"
    source = ROOT / "modernization/backups/save-recovery/1790661735830701800/test2.sav"
    if sha(runtime / "ddraw.dll") != WRAPPER_SHA or sha(source) != FIXTURE_SHA:
        raise RuntimeError("Unexpected wrapper or fixture")
    if fixture.exists():
        raise RuntimeError("An existing test2 save must remain untouched")
    out = ROOT / "modernization/assets/hd/battle-sharpen-trial" / str(time.time_ns())
    out.mkdir(parents=True)
    data = {"wrapper_sha256": WRAPPER_SHA, "fixture_sha256": FIXTURE_SHA, "samples": []}
    try:
        fixture.write_bytes(source.read_bytes())
        for level in ("0", "1", "2", "0", "1"):
            os.environ["MM_PROBE_BATTLE_SHARPEN"] = level
            run = out / f"sample-{len(data['samples'])}-{level}"
            run.mkdir()
            with CaptureSession("hd", run, "mixed-ui-v4") as session:
                session.load_fixture("test2", False)
                time.sleep(1)
                before_cpu, before_uploads, before_wall = cpu_seconds(session), uploads(session), time.perf_counter()
                time.sleep(10)
                after_wall, after_uploads, after_cpu = time.perf_counter(), uploads(session), cpu_seconds(session)
                elapsed = after_wall - before_wall
                data["samples"].append({"level": int(level), "wall_seconds": elapsed,
                                        "engine_cpu_seconds": after_cpu - before_cpu,
                                        "d3d9_uploads": after_uploads - before_uploads,
                                        "uploads_per_second": (after_uploads - before_uploads) / elapsed})
                print(data["samples"][-1], flush=True)
        (out / "performance.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(out, flush=True)
    finally:
        os.environ.pop("MM_PROBE_BATTLE_SHARPEN", None)
        if fixture.exists() and sha(fixture) == FIXTURE_SHA:
            fixture.unlink()


if __name__ == "__main__":
    main()
