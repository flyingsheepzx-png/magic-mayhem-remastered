"""Add read-only DirectDraw geometry logging to a pinned diagnostic wrapper checkout.

Run on a disposable checkout of cnc-ddraw commit 279a057; this never changes
the installed game or community wrapper. The background-input patch is applied
to the same disposable checkout before building its DLL.
"""
from pathlib import Path
import subprocess
import sys

ROOT = (Path(__file__).resolve().parents[2] / "game")
PIN = "279a057ee7e1e4d584b56141c014ab01f3c6ee6d"


def main():
    source = Path(sys.argv[1]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source,
                                   text=True).strip()
    if head != PIN:
        raise SystemExit("Unknown cnc-ddraw revision")
    target = source / "src/IDirectDraw/IDirectDraw.c"
    data = target.read_text(encoding="utf-8")
    if "mm_hd_geometry_log" in data:
        raise SystemExit("Geometry logger already applied")
    if (source / "src/mm_background.h").exists():
        raise SystemExit("Background patch already applied")
    subprocess.run([sys.executable, str(ROOT / "modernization/wrapper-probe/apply_background_input.py"),
                    str(source)], check=True)
    needle = '#include "debug.h"'
    helper = r'''

/* Opt-in, read-only DirectDraw call geometry. No game surface is modified. */
static void mm_hd_geometry_log(char kind, unsigned width, unsigned height,
                               unsigned bpp, unsigned caps, void* caller,
                               void* caller_of_surface_helper)
{
    char line[128];
    DWORD written;
    int length;
    HANDLE file;
    if (!GetEnvironmentVariableA("MM_HD_GEOMETRY_LOG", NULL, 0)) return;
    length = _snprintf(line, sizeof(line), "%c,%08X,%08X,%u,%u,%u,%08X\r\n",
                       kind, (unsigned)caller, (unsigned)caller_of_surface_helper,
                       width, height, bpp, caps);
    if (length <= 0) return;
    file = CreateFileA("modernization\\assets\\hd\\directdraw-geometry.csv",
                       FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                       NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    WriteFile(file, line, (DWORD)length, &written, NULL);
    CloseHandle(file);
}
'''
    if data.count(needle) != 1:
        raise SystemExit("Unexpected DirectDraw include site")
    data = data.replace(needle, needle + helper, 1)
    needle = "    HRESULT ret = \n        dd_CreateSurface("
    insert = """    if (lpDDSurfaceDesc)
        mm_hd_geometry_log('S', lpDDSurfaceDesc->dwWidth,
                           lpDDSurfaceDesc->dwHeight,
                           lpDDSurfaceDesc->ddpfPixelFormat.dwRGBBitCount,
                           lpDDSurfaceDesc->ddsCaps.dwCaps, _ReturnAddress(),
                           _ReturnAddress() == (void*)0x58ADC5 ?
                               ((void**)_AddressOfReturnAddress())[266] : NULL);

"""
    if data.count(needle) != 1:
        raise SystemExit("Unexpected CreateSurface site")
    data = data.replace(needle, insert + needle, 1)
    needle = "    HRESULT ret = dd_SetDisplayMode(dwWidth, dwHeight, dwBPP, SDM_MODE_SET_BY_GAME);"
    if data.count(needle) != 2:
        raise SystemExit("Unexpected SetDisplayMode sites")
    data = data.replace(needle,
                        "    mm_hd_geometry_log('M', dwWidth, dwHeight, dwBPP, 0, _ReturnAddress(), NULL);\n" + needle)
    target.write_text(data, encoding="utf-8", newline="\n")
    print("Applied read-only DirectDraw geometry logger")


if __name__ == "__main__":
    main()
