"""Read-only engine counter sampling for the verified community build.

This samples candidate engine counters, NOT presented frames or unique visual
frames. Use surface-update instrumentation before claiming real rendering FPS.
"""
import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import time

ROOT = (Path(__file__).resolve().parents[2] / "game")
SUPPORTED = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
ADDRESSES = {
    "logic_rate_config": 0x6DE6FD,
    "logic_interval_ms_config": 0x6DE6F9,
    "loop_counter_window_candidate": 0x6E80F0,
    "display_counter_window_candidate": 0x6E80F4,
    "scheduler_interval_ms_candidate": 0x6DBE95,
    "route_search_limit": 0x5E174C,
    "route_other_limit_candidate": 0x5E1748,
    "high_resolution_flag": 0x6DE6D5,
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    if args.seconds <= 0:
        raise SystemExit("seconds must be positive")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000 | 0x10, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD(32768)
        path = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        exe = Path(path.value)
        if exe.resolve() != (ROOT / "Chaos.exe").resolve():
            raise RuntimeError("PID does not belong to this game's executable")
        digest = hashlib.sha256(exe.read_bytes()).hexdigest()
        if digest != SUPPORTED:
            raise RuntimeError("Unsupported executable; refusing address-based sampling")
        def read32(address):
            value = wintypes.DWORD()
            count = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, address, ctypes.byref(value), 4,
                                            ctypes.byref(count)) or count.value != 4:
                raise ctypes.WinError(ctypes.get_last_error())
            return value.value
        rows = []
        start = time.perf_counter()
        while True:
            elapsed = time.perf_counter() - start
            try:
                values = [read32(address) for address in ADDRESSES.values()]
            except OSError as exc:
                raise RuntimeError("Game exited or image address changed while sampling") from exc
            rows.append([elapsed, *values])
            if elapsed >= args.seconds:
                break
            time.sleep(0.004)
        output = ROOT / "modernization" / "logs"
        output.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        csv_path = output / f"engine-counters-{stamp}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["seconds", *ADDRESSES])
            writer.writerows(rows)
        loop_index = list(ADDRESSES).index("loop_counter_window_candidate") + 1
        changes = sum(a[loop_index] != b[loop_index] for a, b in zip(rows, rows[1:]))
        duration = rows[-1][0] - rows[0][0]
        per_counter = {}
        for offset, name in enumerate(ADDRESSES, start=1):
            values = [row[offset] for row in rows]
            positive = [b - a for a, b in zip(values, values[1:]) if b >= a]
            per_counter[name] = {"first": values[0], "last": values[-1],
                                 "maximum": max(values), "resets": sum(b < a for a, b in zip(values, values[1:])),
                                 "positive_increments": sum(positive)}
        summary = {"exe_sha256": digest, "duration_seconds": duration,
                   "samples": len(rows), "candidate_counter_changes": changes,
                   "candidate_change_rate": changes / duration,
                   "counters": per_counter,
                   "first_values": dict(zip(ADDRESSES, rows[0][1:])),
                   "last_values": dict(zip(ADDRESSES, rows[-1][1:])),
                   "is_render_fps_measurement": False}
        csv_path.with_suffix(".json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        print(csv_path)
    finally:
        kernel.CloseHandle(handle)

if __name__ == "__main__":
    main()
