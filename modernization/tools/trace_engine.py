"""Bounded, hash-gated x86 hardware-breakpoint trace of an owned Chaos.exe.

No executable bytes are patched. Windows suspends the debuggee briefly at each
breakpoint, so measured wall-clock timing includes debugger overhead. Counts and
ordering are diagnostic only; this is not an FPS or movement-speed benchmark.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct
import time

ROOT = (Path(__file__).resolve().parents[2] / "game")
SUPPORTED = "b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291"
SITES = {
    "battle_scene_iteration": 0x46AFC0,
    "unit_update_candidate": 0x509E50,
    "route_work": 0x5128A0,
    "draw_candidate": 0x4D9BA0,
}
CONTEXT_FLAGS = 0x10013  # WOW64_CONTROL | INTEGER | DEBUG_REGISTERS
EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
EXCEPTION_SINGLE_STEP = 0x80000004
EXCEPTION_BREAKPOINT = 0x80000003
STATUS_WX86_SINGLE_STEP = 0x4000001E
STATUS_WX86_BREAKPOINT = 0x4000001F
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
THREAD_CONTEXT_ACCESS = 0x0008 | 0x0010 | 0x0002 | 0x0040
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenThread.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.Wow64GetThreadContext.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel.Wow64GetThreadContext.restype = wintypes.BOOL
    kernel.Wow64SetThreadContext.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel.Wow64SetThreadContext.restype = wintypes.BOOL
    kernel.DebugActiveProcess.argtypes = [wintypes.DWORD]
    kernel.DebugActiveProcess.restype = wintypes.BOOL
    kernel.DebugActiveProcessStop.argtypes = [wintypes.DWORD]
    kernel.DebugActiveProcessStop.restype = wintypes.BOOL
    kernel.DebugSetProcessKillOnExit.argtypes = [wintypes.BOOL]
    kernel.DebugSetProcessKillOnExit.restype = wintypes.BOOL
    kernel.WaitForDebugEvent.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    kernel.WaitForDebugEvent.restype = wintypes.BOOL
    kernel.ContinueDebugEvent.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
    kernel.ContinueDebugEvent.restype = wintypes.BOOL
    for name in ("SuspendThread", "ResumeThread"):
        getattr(kernel, name).argtypes = [wintypes.HANDLE]
        getattr(kernel, name).restype = wintypes.DWORD
    kernel.GetExitCodeThread.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeThread.restype = wintypes.BOOL
    return kernel


def checked_file(kernel, pid):
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        path = Path(buffer.value)
        if path.resolve() != (ROOT / "Chaos.exe").resolve():
            raise RuntimeError("PID is not this game's executable")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != SUPPORTED:
            raise RuntimeError("Unsupported executable hash; trace refused")
        return digest
    finally:
        kernel.CloseHandle(handle)


def thread_context(kernel, tid, sites, install=False, clear_status=False, originals=None, watches=()):
    handle = kernel.OpenThread(THREAD_CONTEXT_ACCESS, False, tid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        context = (wintypes.DWORD * 179)()  # 716-byte WOW64_CONTEXT
        context[0] = CONTEXT_FLAGS
        if not kernel.Wow64GetThreadContext(handle, ctypes.byref(context)):
            raise ctypes.WinError(ctypes.get_last_error())
        dr6, eip = context[5], context[46]
        if install:
            if context[6] & 0xFF:
                raise RuntimeError("Existing hardware breakpoints; refusing to overwrite")
            originals[tid] = (handle, tuple(context[1:7]))
            for index, address in enumerate(sites.values(), start=1):
                context[index] = address
            context[5] = 0
            context[6] = sum(1 << (2 * index) for index in range(len(sites)))
            context[6] |= sum(1 << (16 + 4 * index) for index, name in enumerate(sites)
                              if name in watches)  # RW=write, LEN=one byte
        elif clear_status:
            context[5] = 0
            # Win32/WOW64 may re-enter an execute breakpoint at the same EIP
            # unless Resume Flag is set for the next instruction.
            context[48] |= 0x10000
        if install or clear_status:
            if not kernel.Wow64SetThreadContext(handle, ctypes.byref(context)):
                raise ctypes.WinError(ctypes.get_last_error())
        registers = dict(zip(("edi", "esi", "ebx", "edx", "ecx", "eax", "ebp"), context[39:46]))
        registers["esp"] = context[49]
        return dr6, eip, registers
    finally:
        if originals is None or tid not in originals:
            kernel.CloseHandle(handle)


def restore_threads(kernel, originals, errors):
    """Restore only debug registers, retaining current control/register state."""
    suspended = []
    try:
        # Hold every live instrumented thread before removing breakpoints.
        for tid, (handle, registers) in originals.items():
            exit_code = wintypes.DWORD()
            if not kernel.GetExitCodeThread(handle, ctypes.byref(exit_code)):
                errors.append(f"thread {tid} exit query failed")
                continue
            if exit_code.value != 259:  # STILL_ACTIVE
                continue
            if kernel.SuspendThread(handle) == 0xFFFFFFFF:
                errors.append(f"thread {tid} cleanup suspend failed")
                continue
            suspended.append((tid, handle, registers))
        for tid, handle, registers in suspended:
            context = (wintypes.DWORD * 179)()
            context[0] = 0x10010  # debug registers only
            for index, value in enumerate(registers, 1):
                context[index] = value
            if not kernel.Wow64SetThreadContext(handle, ctypes.byref(context)):
                errors.append(f"thread {tid} debug-register restore failed")
    finally:
        for tid, handle, _ in suspended:
            if kernel.ResumeThread(handle) == 0xFFFFFFFF:
                errors.append(f"thread {tid} cleanup resume failed")
        for handle, _ in originals.values():
            kernel.CloseHandle(handle)
        originals.clear()


def trace(pid, seconds, output, sites=None, watch_unit0=False, watch_unit0_state=False,
          watch_unit0_render=False, watch_memory=None):
    if seconds <= 0 or seconds > 60:
        raise ValueError("Trace duration must be 0 < seconds <= 60")
    kernel = api()
    digest = checked_file(kernel, pid)
    sites = dict(sites or SITES)
    if not 1 <= len(sites) <= 4 or any(not 0x400000 <= a < 0x5C0000 for a in sites.values()):
        raise ValueError("Specify one to four executable addresses in the known image")
    watches = {}
    unit0 = None
    if watch_memory is not None:
        if any((watch_unit0, watch_unit0_state, watch_unit0_render)) or len(sites) > 3:
            raise ValueError("A memory watch needs at most three executable sites and no unit watch")
        if not 0x10000 <= watch_memory < 0x80000000:
            raise ValueError("Memory watch outside 32-bit user address range")
        kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        kernel.ReadProcessMemory.restype = wintypes.BOOL
        handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | 0x10, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            value = ctypes.c_ubyte()
            size = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, watch_memory, ctypes.byref(value), 1,
                                            ctypes.byref(size)) or size.value != 1:
                raise ValueError("Memory watch address is unreadable")
        finally:
            kernel.CloseHandle(handle)
        watches = {"surface_pixel_write": watch_memory}
        sites.update(watches)
    if watch_unit0 or watch_unit0_state or watch_unit0_render:
        if sum((watch_unit0,watch_unit0_state,watch_unit0_render)) != 1:
            raise ValueError("Choose one unit write watch set")
        if len(sites) != 1:
            raise ValueError("Route writes require exactly one executable site (three slots reserved)")
        kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        kernel.ReadProcessMemory.restype = wintypes.BOOL
        handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | 0x10, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            def read32(address):
                value = wintypes.DWORD()
                size = ctypes.c_size_t()
                if not kernel.ReadProcessMemory(handle, address, ctypes.byref(value), 4,
                                                ctypes.byref(size)) or size.value != 4:
                    raise ctypes.WinError(ctypes.get_last_error())
                return value.value
            unit0, count = read32(0x6DEF58), read32(0x6DEF5C)
            if not 0x10000 <= unit0 < 0x80000000 or not 0 < count <= 1024:
                raise ValueError("Unit table failed validation")
            watches = ({"unit0_render_y_write":unit0+0xB7F}
                       if watch_unit0_render else
                       {"unit0_motion_state_write": unit0 + 0x5F0,
                        "unit0_pending_write": unit0 + 0x688,
                        "unit0_order_gate_write": unit0 + 0x618}
                       if watch_unit0_state else
                       {"unit0_active_write": unit0 + 0xB8B,
                        "unit0_destination_write": unit0 + 0x96B,
                        "unit0_count_write": unit0 + 0x97B})
            if any(name in sites for name in watches):
                raise ValueError("Reserved watch name")
            sites.update(watches)
        finally:
            kernel.CloseHandle(handle)
    if not kernel.DebugActiveProcess(pid):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                         ctypes.c_void_p, ctypes.c_size_t,
                                         ctypes.POINTER(ctypes.c_size_t)]
    kernel.ReadProcessMemory.restype = wintypes.BOOL
    stack_handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | 0x10, False, pid)
    if not stack_handle:
        kernel.DebugActiveProcessStop(pid)
        raise ctypes.WinError(ctypes.get_last_error())

    def stack_word(address):
        if not 0x10000 <= address < 0x80000000:
            return None
        value = wintypes.DWORD()
        size = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(stack_handle, address, ctypes.byref(value), 4,
                                        ctypes.byref(size)) or size.value != 4:
            return None
        return value.value
    def memory_byte(address):
        value = ctypes.c_ubyte()
        size = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(stack_handle, address, ctypes.byref(value), 1,
                                        ctypes.byref(size)) or size.value != 1:
            return None
        return value.value
    events = []
    errors = []
    debug_events = []
    exception_counts = {}
    process_exit_code = None
    installed_threads = set()
    originals = {}
    pending = None
    frequency = ctypes.c_longlong()
    kernel.QueryPerformanceFrequency(ctypes.byref(frequency))
    start_qpc = ctypes.c_longlong()
    kernel.QueryPerformanceCounter(ctypes.byref(start_qpc))
    start = time.monotonic()
    try:
        if not kernel.DebugSetProcessKillOnExit(False):
            raise ctypes.WinError(ctypes.get_last_error())
        while time.monotonic() - start < seconds:
            raw = ctypes.create_string_buffer(256)
            if not kernel.WaitForDebugEvent(raw, 100):
                if ctypes.get_last_error() == 121:  # ERROR_SEM_TIMEOUT
                    continue
                raise ctypes.WinError(ctypes.get_last_error())
            code, event_pid, tid = struct.unpack_from("<III", raw, 0)
            pending = (event_pid, tid, DBG_CONTINUE)
            # The debugger owns image/DLL file handles. Windows manages the
            # event process/thread handles; our retained OpenThread handles
            # are closed separately after restoring the debug registers.
            if code in (CREATE_PROCESS_DEBUG_EVENT, LOAD_DLL_DEBUG_EVENT):
                file_handle = struct.unpack_from("<Q", raw, 16)[0]
                if file_handle:
                    kernel.CloseHandle(file_handle)
            if len(debug_events) < 100:
                debug_events.append({"event_code": code, "thread_id": tid,
                                     "value_at_union_start": struct.unpack_from("<I", raw, 16)[0]})
            disposition = DBG_CONTINUE
            if code in (CREATE_PROCESS_DEBUG_EVENT, CREATE_THREAD_DEBUG_EVENT):
                try:
                    thread_context(kernel, tid, sites, install=True, originals=originals, watches=watches)
                    installed_threads.add(tid)
                except (OSError, RuntimeError) as exc:
                    errors.append(f"thread {tid} breakpoint setup: {exc}")
            elif code == EXCEPTION_DEBUG_EVENT:
                exception_code = struct.unpack_from("<I", raw, 16)[0]
                exception_counts[f"0x{exception_code:08x}"] = exception_counts.get(f"0x{exception_code:08x}", 0) + 1
                if exception_code in (EXCEPTION_SINGLE_STEP, STATUS_WX86_SINGLE_STEP) and tid in installed_threads:
                    stamp = ctypes.c_longlong()
                    kernel.QueryPerformanceCounter(ctypes.byref(stamp))
                    try:
                        dr6, eip, registers = thread_context(kernel, tid, sites, clear_status=True)
                        player = stack_word(0x6DEF58)
                        player_fields = ([stack_word(player + offset) for offset in
                                          (8, 12, 16, 0x14, 0x18, 0xB8B, 0x618)]
                                         if player and registers["ecx"] == player else None)
                        for index, (name, address) in enumerate(sites.items()):
                            if dr6 & (1 << index):
                                events.append((stamp.value, tid, name, eip, address,
                                               registers, stack_word(registers["esp"]),
                                               [stack_word(registers["esp"] + offset)
                                                for offset in (4, 8, 12, 16)], player_fields,
                                               [stack_word(registers["esp"] + offset)
                                                for offset in range(0, 128, 4)]
                                               if name in ("surface_pixel_write", "draw_project") else None,
                                               [memory_byte(address + byte) for byte in (0, 1)]
                                               if name == "surface_pixel_write" else None))
                        if not dr6 & 0xF:
                            errors.append(f"Single-step without DR6 site on thread {tid}: EIP={eip:08x}")
                    except OSError as exc:
                        errors.append(f"thread {tid} context read: {exc}")
                        disposition = DBG_EXCEPTION_NOT_HANDLED
                elif exception_code not in (EXCEPTION_BREAKPOINT, STATUS_WX86_BREAKPOINT):
                    disposition = DBG_EXCEPTION_NOT_HANDLED
            elif code == EXIT_PROCESS_DEBUG_EVENT:
                process_exit_code = struct.unpack_from("<I", raw, 16)[0]
                if not kernel.ContinueDebugEvent(event_pid, tid, disposition):
                    raise ctypes.WinError(ctypes.get_last_error())
                pending = None
                break
            elif code == EXIT_THREAD_DEBUG_EVENT:
                installed_threads.discard(tid)
                previous = originals.pop(tid, None)
                if previous:
                    kernel.CloseHandle(previous[0])
            pending = (event_pid, tid, disposition)
            if not kernel.ContinueDebugEvent(event_pid, tid, disposition):
                raise ctypes.WinError(ctypes.get_last_error())
            pending = None
    except Exception as exc:
        errors.append(f"trace failed: {type(exc).__name__}: {exc}")
    finally:
        restore_threads(kernel, originals, errors)
        if pending and not kernel.ContinueDebugEvent(*pending):
            errors.append("Failed to continue pending event during cleanup")
        if process_exit_code is None and not kernel.DebugActiveProcessStop(pid):
            errors.append("Debugger detach failed")
        kernel.CloseHandle(stack_handle)
    result = {"exe_sha256": digest, "pid": pid, "sites": sites,
              "write_watch_sites": watches, "unit0_address": unit0,
              "start_qpc": start_qpc.value, "qpc_frequency": frequency.value,
              "duration_seconds": time.monotonic() - start,
              "counts": {name: sum(e[2] == name for e in events) for name in sites},
              "events": [{"qpc": qpc, "seconds": (qpc - start_qpc.value) / frequency.value,
                          "thread_id": tid, "site": name, "eip": eip, "address": address,
                          "registers": registers, "stack_word_at_entry": stack_value,
                          "stack_arguments_candidate": stack_arguments,
                          "unit0_fields_candidate": player_fields,
                          "stack_words": stack_words, "watched_pixel_bytes": pixel_bytes}
                         for qpc, tid, name, eip, address, registers, stack_value,
                             stack_arguments, player_fields, stack_words, pixel_bytes in events],
              "errors": errors, "debugger_overhead_present": True,
              "debug_events": debug_events, "process_exit_code": process_exit_code,
              "exception_counts": exception_counts,
              "valid_trace": bool(events) and not errors and process_exit_code is None,
              "gameplay_speed_verified": False, "render_fps_measured": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--seconds", type=float, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "modernization/logs/engine-trace.json")
    parser.add_argument("--site", action="append", default=[], metavar="NAME=VA",
                        help="Override default sites (one to four known-image VAs)")
    parser.add_argument("--watch-unit0-route", action="store_true",
                        help="Use three slots for byte-write breakpoints on hash-gated unit0 route fields")
    parser.add_argument("--watch-unit0-state", action="store_true",
                        help="Watch unit0 motion/pending/order-gate state writes")
    parser.add_argument("--watch-unit0-render", action="store_true",
                        help="Watch writes to unit0's rendered Y offset")
    parser.add_argument("--watch-memory", type=lambda value: int(value, 0),
                        help="Read-validated byte write watch in the owned process")
    args = parser.parse_args()
    sites = {}
    for item in args.site:
        name, sep, address = item.partition("=")
        if not sep or not name or name in sites:
            parser.error(f"Invalid or duplicate site: {item}")
        sites[name] = int(address, 0)
    result = trace(args.pid, args.seconds, args.output, sites or None,
                   args.watch_unit0_route, args.watch_unit0_state,
                   args.watch_unit0_render, args.watch_memory)
    print(json.dumps({key: result[key] for key in ("counts", "duration_seconds", "errors", "process_exit_code", "exception_counts")}))
    print(args.output)
    if not result["valid_trace"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
