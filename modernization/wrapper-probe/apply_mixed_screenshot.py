"""Make the ordinary screenshot hotkey capture the mixed presentation buffer."""
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "build/cnc-ddraw-src"
path = root / "src/keyboard.c"
source = path.read_text(encoding="utf-8")
helper = '''
static BOOL mm_keyboard_screenshot(void)
{
    BOOL saved;
    EnterCriticalSection(&g_ddraw.cs);
    if (g_config.lock_surfaces && g_ddraw.primary)
        EnterCriticalSection(&g_ddraw.primary->cs);
    saved = ss_take_screenshot(mm_mixed_present(g_ddraw.primary));
    if (g_config.lock_surfaces && g_ddraw.primary)
        LeaveCriticalSection(&g_ddraw.primary->cs);
    LeaveCriticalSection(&g_ddraw.cs);
    return saved;
}

'''
if "static BOOL mm_keyboard_screenshot" not in source:
    if source.count("ss_take_screenshot(g_ddraw.primary);") != 2:
        raise RuntimeError("Unexpected keyboard screenshot source")
    source = source.replace('#include "screenshot.h"', '#include "screenshot.h"\n#include "mm_mixed.h"')
    source = source.replace("HHOOK g_keyboard_hook;", helper + "HHOOK g_keyboard_hook;")
    source = source.replace("ss_take_screenshot(g_ddraw.primary);", "mm_keyboard_screenshot();")
    path.write_text(source, encoding="utf-8")
print(path)
wnd = root / "src/wndproc.c"
source = wnd.read_text(encoding="utf-8")
if "WM_APP + 79" not in source:
    marker = '        if (wParam == WM_APP + 78)'
    if source.count(marker) != 1:
        raise RuntimeError("Unexpected background screenshot source")
    source = source.replace('#include "mm_mixed.h"', '#include "mm_mixed.h"\n#include "keyboard.h"')
    source = source.replace(marker, '''        if (wParam == WM_APP + 79)
        {
            keyboard_hook_proc(HC_ACTION, g_config.hotkeys.screenshot,
                g_config.hotkeys.screenshot == VK_SNAPSHOT ? (LPARAM)0xC0000001 : (LPARAM)1);
            return 0x4D4D4247;
        }
''' + marker)
    wnd.write_text(source, encoding="utf-8")
print(wnd)
