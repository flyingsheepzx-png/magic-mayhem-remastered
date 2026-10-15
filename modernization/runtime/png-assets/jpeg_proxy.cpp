#define WIN32_LEAN_AND_MEAN
#include <windows.h>
extern "C" __declspec(dllimport) void __cdecl mm_png_assets_anchor();
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID){if(reason==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(instance);mm_png_assets_anchor();}return TRUE;}
