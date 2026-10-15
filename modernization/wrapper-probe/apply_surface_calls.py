"""Add bounded DirectDraw COM caller telemetry to pinned diagnostic source."""
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
if head != "279a057ee7e1e4d584b56141c014ab01f3c6ee6d":
    raise SystemExit("Unsupported upstream revision")
target = source / "src/IDirectDraw/IDirectDrawSurface.c"
data = target.read_text(encoding="utf-8")
if "mm_surface_call(" in data:
    raise SystemExit("Surface-call instrumentation already applied")
needle = '#include "debug.h"'
function = r'''

/* Per-callsite diagnostics. This logs game-origin COM calls, not successful
 * presents. The record is a single append write to avoid cross-thread CSV
 * fragments; missing early events are acceptable for bounded diagnostics. */
static void mm_surface_call(char kind, IDirectDrawSurfaceImpl* surface, void* caller)
{
    LARGE_INTEGER tick;
    char line[128];
    DWORD written;
    int length;
    HANDLE file;
    if (!surface) return;
    QueryPerformanceCounter(&tick);
    length = _snprintf(line, sizeof(line), "%I64d,%c,%08X,%d\r\n",
                       tick.QuadPart, kind, (unsigned int)caller,
                       !!(surface->caps & DDSCAPS_PRIMARYSURFACE));
    if (length <= 0) return;
    file = CreateFileA("modernization\\logs\\surface-calls.csv",
                       FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                       NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    WriteFile(file, line, (DWORD)length, &written, NULL);
    CloseHandle(file);
}

/* Hash the completed 16-bit primary image at each game BltFast call. */
static void mm_surface_hash(IDirectDrawSurfaceImpl* surface, void* caller)
{
    if (GetEnvironmentVariableA("MM_PROBE_LIGHT", NULL, 0)) return;
    const unsigned char* row;
    unsigned hash = 2166136261u;
    int y, x, bytes;
    char line[128];
    DWORD written;
    int length;
    LARGE_INTEGER tick;
    HANDLE file;
    if (!surface || !(surface->caps & DDSCAPS_PRIMARYSURFACE) ||
        !surface->surface || surface->width != 800 || surface->height != 600 ||
        surface->bytes_pp != 2) return;
    row = (const unsigned char*)surface->surface;
    bytes = surface->width * surface->bytes_pp;
    for (y = 0; y < surface->height; ++y, row += surface->pitch)
        for (x = 0; x < bytes; ++x)
            hash = (hash ^ row[x]) * 16777619u;
    QueryPerformanceCounter(&tick);
    length = _snprintf(line, sizeof(line), "%I64d,%08X,%08X,%u\r\n",
                       tick.QuadPart, (unsigned int)caller, hash,
                       (unsigned)GetCurrentThreadId());
    if (length <= 0) return;
    file = CreateFileA("modernization\\logs\\surface-blt-hashes.csv",
                       FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                       NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    WriteFile(file, line, (DWORD)length, &written, NULL);
    CloseHandle(file);
}
'''
if data.count(needle) != 1:
    raise SystemExit("Unexpected include site")
data = data.replace(needle, needle + function, 1)
sites = {
    "IDirectDrawSurface__Blt(": "B",
    "IDirectDrawSurface__BltFast(": "F",
    "IDirectDrawSurface__Flip(": "P",
    "IDirectDrawSurface__Lock(": "L",
    "IDirectDrawSurface__Unlock(": "U",
    "IDirectDrawSurface__ReleaseDC(": "D",
}
for name, letter in sites.items():
    start = data.index(name)
    body = data.index("{", start)
    data = data[:body+1] + f'\n    mm_surface_call(\'{letter}\', This, _ReturnAddress());' + data[body+1:]
needle = "HRESULT ret = dds_BltFast(This, dwX, dwY, (IDirectDrawSurfaceImpl*)lpDDSrcSurface, lpSrcRect, dwFlags);"
if data.count(needle) != 1:
    raise SystemExit("Unexpected BltFast call site")
data = data.replace(needle, needle + "\n    if (ret == DD_OK) mm_surface_hash(This, _ReturnAddress());", 1)
needle = "HRESULT ret = dds_Lock(This, lpDestRect, (LPDDSURFACEDESC)lpDDSurfaceDesc, dwFlags, hEvent);"
if data.count(needle) != 1:
    raise SystemExit("Unexpected Lock call site")
lock_memory = r'''
    if (ret == DD_OK && lpDDSurfaceDesc) {
        LARGE_INTEGER tick;
        char line[160];
        DWORD written;
        HANDLE file;
        QueryPerformanceCounter(&tick);
        int length = _snprintf(line, sizeof(line), "%I64d,M,%08X,%d,%08X,%d,%d,%d\r\n",
            tick.QuadPart, (unsigned int)_ReturnAddress(),
            !!(This->caps & DDSCAPS_PRIMARYSURFACE),
            (unsigned int)lpDDSurfaceDesc->lpSurface,
            (int)lpDDSurfaceDesc->lPitch,
            (int)lpDDSurfaceDesc->dwWidth,
            (int)lpDDSurfaceDesc->dwHeight);
        if (length > 0) {
            file = CreateFileA("modernization\\logs\\surface-calls.csv", FILE_APPEND_DATA,
                FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS,
                FILE_ATTRIBUTE_NORMAL, NULL);
            if (file != INVALID_HANDLE_VALUE) {
                WriteFile(file, line, (DWORD)length, &written, NULL);
                CloseHandle(file);
            }
        }
    }
'''
data = data.replace(needle, needle + lock_memory, 1)
target.write_text(data, encoding="utf-8", newline="\n")
print("Added DirectDraw surface caller telemetry")
