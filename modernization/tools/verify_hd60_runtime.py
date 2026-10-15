"""Bounded read-only startup check for the isolated HD plus 30/60 candidate."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

import capstone
from PIL import Image
import pefile

LAB = (Path(__file__).resolve().parents[2] / "game")
ENTRY = LAB / "Chaos-HD60-Trial.exe"
ENGINE = LAB / "Chaos-HD60-engine.exe"
RUNTIME = LAB / "modernization/runtime/combined_hd60/combined_hd60.dll"
ENTRY_SHA = "1ebb20d0f53f5e73532c02edfd68d81f4b3f7cf06c99081e90b3d6548807c4bf"
ENGINE_SHA = "be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7"
RUNTIME_SHA = "ba24cab91e716495f88780625d0eed4344009de2baca81d9497da3ac05130f0f"
HOOKS = (0x50FCEC, 0x5106DA, 0x512460, 0x4FA261, 0x4FA622,
         0x4FFF41, 0x5108C9, 0x4FD552, 0x4FD5A6, 0x5104D1, 0x46B488)
STATIC_LAYOUT = {
    0x54FDC0: 960, 0x4DD6FE: 720, 0x4DD710: 960,
    0x573A1E: 960, 0x573A35: 720,  # plus the original high-res offsets => 1120x840
    0x46AA8E: 670, 0x46AA9E: 122,
    0x47096B: 670, 0x47097D: 122,
    0x4713B5: 670, 0x4713C9: 122,
    0x471B16: 670, 0x471B28: 122,
    0x4DC4E7: 837, 0x4DC4EF: 50,
    0x4DC548: 837, 0x4DC550: 50,
    0x4DC56B: 837, 0x4DC575: 50,
    0x4DC611: 837, 0x4DC622: 837, 0x4DC62A: 837,
}


class ProcessEntry(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong), ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.c_ulong), ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong), ("szExeFile", ctypes.c_wchar * 260)]


def processes(kernel):
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    rows = []
    try:
        if kernel.Process32FirstW(handle, ctypes.byref(entry)):
            while True:
                rows.append((entry.th32ProcessID, entry.th32ParentProcessID,
                             entry.szExeFile.lower()))
                if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                    break
    finally:
        kernel.CloseHandle(handle)
    return rows


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configured_kernel():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessEntry)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_void_p, ctypes.c_size_t,
                                        ctypes.POINTER(ctypes.c_size_t)]
    kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    return kernel


def read(kernel, handle, address, n):
    buffer = (ctypes.c_ubyte * n)()
    count = ctypes.c_size_t()
    if not kernel.ReadProcessMemory(handle, ctypes.c_void_p(address),
                                    ctypes.byref(buffer), n, ctypes.byref(count)) or count.value != n:
        raise ctypes.WinError(ctypes.get_last_error())
    return bytes(buffer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        help="optional JSON report path inside the project")
    args = parser.parse_args()
    if args.report and not args.report.resolve().is_relative_to(LAB.parent.resolve()):
        raise RuntimeError("Report path must stay inside the project")
    if (sha(ENTRY) != ENTRY_SHA or sha(ENGINE) != ENGINE_SHA or
            sha(RUNTIME) != RUNTIME_SHA):
        raise RuntimeError("Unknown isolated candidate files")
    engine_data = ENGINE.read_bytes()
    pe = pefile.PE(data=engine_data)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    decoder.detail = True
    static_values = {}
    for address, expected in STATIC_LAYOUT.items():
        offset = pe.get_offset_from_rva(address - pe.OPTIONAL_HEADER.ImageBase)
        instruction = next(decoder.disasm(engine_data[offset:offset + 15], address, count=1))
        operand = instruction.operands[-1]
        actual = operand.imm if operand.type == capstone.x86.X86_OP_IMM else None
        static_values[hex(address)] = actual
        if actual != expected:
            raise RuntimeError(f"Static layout gate failed at {address:#x}: {actual} != {expected}")
    progress_sizes = {}
    for path in sorted((LAB / "Interface/ProgressIndicator").glob("* Progress Bar*.JPG")):
        with Image.open(path) as image:
            progress_sizes[path.name] = list(image.size)
    if len(progress_sizes) != 8 or any(size != [840, 50] for size in progress_sizes.values()):
        raise RuntimeError("Loading progress resources are not all 840x50")
    mini_menu = LAB / "Interface/MiniMenu/800x600/Realm View Mini Menu 800-600.BMP"
    with Image.open(mini_menu) as image:
        mini_menu_size = list(image.size)
    if mini_menu_size != [840, 560]:
        raise RuntimeError("ESC menu background is not 840x560")
    prefs = (LAB / "CFG/prefs.cfg").read_text(encoding="cp1252")
    if "MaxFramesPerSec=30" not in prefs.splitlines():
        raise RuntimeError("Authorized MaxFramesPerSec=30 default is missing")
    kernel = configured_kernel()
    if any(name in ("chaos.exe", "chaos-singleplayer-600.exe", "chaos-hd60-engine.exe")
           for _, _, name in processes(kernel)):
        raise RuntimeError("Close other game processes before verification")
    entry = subprocess.Popen([str(ENTRY)], cwd=LAB)
    child = None
    result = {
        "entry": str(ENTRY), "entry_pid": entry.pid,
        "hashes": {"entry": ENTRY_SHA, "engine": ENGINE_SHA, "runtime": RUNTIME_SHA},
        "static_layout_values": static_values,
        "speech_click_area": [1120, 840],
        "loading_progress_resources": progress_sizes,
        "mini_menu_size": mini_menu_size,
        "max_frames_per_sec": 30,
    }
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            matches = [pid for pid, parent, name in processes(kernel)
                       if parent == entry.pid and name == "chaos-hd60-engine.exe"]
            if matches:
                child = matches[0]
                break
            if entry.poll() is not None:
                raise RuntimeError(f"Entry exited early: {entry.returncode}")
            time.sleep(0.2)
        if child is None:
            raise RuntimeError("HD60 engine child was not started")
        result["engine_pid"] = child
        handle = kernel.OpenProcess(0x1011, 0, child)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            time.sleep(2)
            result["hooks"] = {hex(va): read(kernel, handle, va, 1).hex() == "e9"
                               for va in HOOKS}
            result["all_hooks_loaded"] = all(result["hooks"].values())
            width = int.from_bytes(read(kernel, handle, 0x6A49F0, 4), "little")
            height = int.from_bytes(read(kernel, handle, 0x6A49F4, 4), "little")
            result["surface"] = [width, height]
            if not result["all_hooks_loaded"] or [width, height] != [1120, 840]:
                raise RuntimeError("Combined startup gate failed")
        finally:
            kernel.TerminateProcess(handle, 0)
            kernel.CloseHandle(handle)
    finally:
        if entry.poll() is None:
            try:
                entry.wait(timeout=5)
            except subprocess.TimeoutExpired:
                entry.terminate()
                entry.wait(timeout=5)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
