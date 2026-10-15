"""Reapply the ordinary message-position fix and read-only surface telemetry.

Run after the existing mixed-render and background-input wrapper patches.
Reject unknown source instead of partially patching it.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'modernization/build/cnc-ddraw-src/src'
PATCHES={
    'winapi_hooks.c':[
        ('''            lpMsg->pt.x = min(x, g_ddraw.width - 1);
            lpMsg->pt.y = min(y, g_ddraw.height - 1);''',
         '''            POINT mixed = mm_mixed_input_point(g_ddraw.primary,
                min(x, g_ddraw.width - 1), min(y, g_ddraw.height - 1));
            lpMsg->pt.x = mixed.x;
            lpMsg->pt.y = mixed.y;'''),
        ('''            lpMsg->pt.x = x;
            lpMsg->pt.y = y;''',
         '''            /* Message-position polling drives the software cursor. lParam
             * remains in surface coordinates for fake_WndProc's conversion;
             * pt must use the same battle coordinates as GetCursorPos. */
            POINT mixed = mm_mixed_input_point(g_ddraw.primary, x, y);
            lpMsg->pt.x = mixed.x;
            lpMsg->pt.y = mixed.y;''')],
    'wndproc.c':[
        ('''    if (mm_background_enabled() && uMsg == mm_background_message())''',
         '''    if ((mm_background_enabled() || (mm_mixed_enabled() &&
         (wParam == WM_APP + 77 || wParam == WM_APP + 80 || wParam == WM_APP + 81))) &&
        uMsg == mm_background_message())'''),
        ('''        if (wParam == WM_NULL) return 0x4D4D4247;''',
         '''        if (wParam == WM_NULL) return 0x4D4D4247;
        /* Read-only surface telemetry for transient loading-frame capture. */
        if (wParam == WM_APP + 80) return g_ddraw.primary ? (LRESULT)g_ddraw.primary->surface : 0;
        if (wParam == WM_APP + 81) return g_ddraw.primary ? g_ddraw.primary->pitch : 0;''')]
}


def main():
    outputs={}
    for name,patches in PATCHES.items():
        path=SOURCE/name;data=path.read_text(encoding='utf-8')
        for old,new in patches:
            if new in data:continue
            if data.count(old)!=1:raise RuntimeError('Unexpected wrapper source: '+name)
            data=data.replace(old,new)
        outputs[path]=data
    for path,data in outputs.items():path.write_text(data,encoding='utf-8')
    print('Mixed cursor and telemetry patches applied')


if __name__=='__main__':main()
