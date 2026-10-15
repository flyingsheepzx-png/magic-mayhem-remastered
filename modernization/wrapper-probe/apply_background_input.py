"""Apply an opt-in private mouse channel to the pinned diagnostic wrapper tree.

Run after the frame-hash patch. Refuses other upstream revisions or previously
applied input changes. The installed community DLL is never touched here.
"""
from pathlib import Path
import shutil
import subprocess
import sys

PIN = "279a057ee7e1e4d584b56141c014ab01f3c6ee6d"
source = Path(sys.argv[1]).resolve()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
if head != PIN:
    raise SystemExit("Unsupported upstream revision")

changes = {}
for name in ("mouse.c", "winapi_hooks.c", "wndproc.c"):
    path = source / "src" / name
    data = path.read_text(encoding="utf-8")
    if "mm_background" in data:
        raise SystemExit("Background patch already applied")
    changes[path] = data


def replace(path, old, new):
    data = changes[path]
    if data.count(old) != 1:
        raise SystemExit(f"Expected one patch site in {path.name}: {old[:70]}")
    changes[path] = data.replace(old, new, 1)


mouse = source / "src/mouse.c"
hooks = source / "src/winapi_hooks.c"
wnd = source / "src/wndproc.c"
replace(mouse, "BOOL g_mouse_locked;", '#define MM_BACKGROUND_IMPLEMENTATION\n#include "mm_background.h"\n\nBOOL g_mouse_locked;')
for routine in ("void mouse_lock()", "void mouse_unlock()"):
    replace(mouse, routine + "\n{", routine + "\n{\n    if (mm_background_enabled()) return;")
replace(hooks, '#include "palette.h"', '#include "palette.h"\n#include "mm_background.h"')
replace(hooks, "BOOL WINAPI fake_GetCursorPos(LPPOINT lpPoint)\n{", """BOOL WINAPI fake_GetCursorPos(LPPOINT lpPoint)
{
    if (mm_background_enabled())
    {
        if (lpPoint)
        {
            lpPoint->x = InterlockedExchangeAdd(&mm_background_x, 0);
            lpPoint->y = InterlockedExchangeAdd(&mm_background_y, 0);
        }
        return TRUE;
    }""")
for routine in ("BOOL WINAPI fake_ClipCursor(const RECT* lpRect)", "BOOL WINAPI fake_SetCursorPos(int X, int Y)",
                "BOOL WINAPI fake_SetForegroundWindow(HWND hWnd)"):
    replace(hooks, routine + "\n{", routine + "\n{\n    if (mm_background_enabled()) return TRUE;")
replace(hooks, "BOOL WINAPI fake_ShowWindow(HWND hWnd, int nCmdShow)\n{",
        "BOOL WINAPI fake_ShowWindow(HWND hWnd, int nCmdShow)\n{\n"
        "    if (mm_background_enabled()) return real_ShowWindow(hWnd, nCmdShow == SW_HIDE ? SW_HIDE : SW_SHOWNOACTIVATE);")
replace(hooks, "    HWND hwnd = real_CreateWindowExA(\n",
        "    if (mm_background_enabled() && !hWndParent) dwExStyle |= WS_EX_NOACTIVATE;\n\n"
        "    HWND hwnd = real_CreateWindowExA(\n")
for routine, key in (("SHORT WINAPI fake_GetKeyState(int nVirtKey)", "nVirtKey"),
                     ("SHORT WINAPI fake_GetAsyncKeyState(int vKey)", "vKey")):
    replace(hooks, routine + "\n{", routine + "\n{\n" + f"""    if (mm_background_enabled() && ({key} == VK_LBUTTON || {key} == VK_RBUTTON))
        return (InterlockedExchangeAdd(&mm_background_buttons, 0) &
                ({key} == VK_LBUTTON ? MK_LBUTTON : MK_RBUTTON)) ? (SHORT)0x8000 : 0;
""")
replace(wnd, '#include "versionhelpers.h"', '#include "versionhelpers.h"\n#include "mm_background.h"')
replace(wnd, "LRESULT CALLBACK fake_WndProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)\n{", """LRESULT CALLBACK fake_WndProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    if (mm_background_enabled() && uMsg == mm_background_message())
    {
        if (wParam == WM_NULL) return 0x4D4D4247;
        if (wParam == WM_APP + 77)
            return ss_take_screenshot(g_ddraw.primary) ? 0x4D4D4247 : 0;
        int x = GET_X_LPARAM(lParam), y = GET_Y_LPARAM(lParam);
        if (x < 0 || y < 0 || x >= (int)g_ddraw.width || y >= (int)g_ddraw.height) return 0;
        LONG buttons = InterlockedExchangeAdd(&mm_background_buttons, 0);
        switch (wParam)
        {
        case WM_MOUSEMOVE: break;
        case WM_LBUTTONDOWN: buttons |= MK_LBUTTON; break;
        case WM_LBUTTONUP: buttons &= ~MK_LBUTTON; break;
        case WM_RBUTTONDOWN: buttons |= MK_RBUTTON; break;
        case WM_RBUTTONUP: buttons &= ~MK_RBUTTON; break;
        default: return 0;
        }
        InterlockedExchange(&mm_background_x, x);
        InterlockedExchange(&mm_background_y, y);
        InterlockedExchange(&mm_background_buttons, buttons);
        InterlockedExchange((LONG*)&g_ddraw.cursor.x, x);
        InterlockedExchange((LONG*)&g_ddraw.cursor.y, y);
        CallWindowProcA(g_ddraw.wndproc, hWnd, (UINT)wParam, buttons, lParam);
        return 0x4D4D4247;
    }
    if (mm_background_enabled() && uMsg >= WM_MOUSEFIRST && uMsg <= WM_MOUSELAST) return 0;
""")

for path, data in changes.items():
    path.write_text(data, encoding="utf-8", newline="\n")
shutil.copyfile(Path(__file__).with_name("mm_background.h"), source / "src/mm_background.h")
print("Applied private diagnostic mouse channel; enable only with MM_PROBE_BACKGROUND_INPUT=1")
