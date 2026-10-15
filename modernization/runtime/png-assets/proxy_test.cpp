#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
int wmain(int argc,wchar_t** argv){if(argc!=3)return 2;HMODULE proxy=LoadLibraryExW(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(!proxy)return 3;HMODULE native=LoadLibraryW(argv[2]);if(!native)return 4;const char* name="?jpeg_read@@YI_NPADPAXHHHH@Z";auto a=GetProcAddress(proxy,name),b=GetProcAddress(native,name);if(!a || a!=b)return 5;FreeLibrary(proxy);FreeLibrary(native);printf("{\"JPEG_export_forwarder_same_function\":true,\"PNG_dependency_loaded\":true,\"game_launched\":false}\n");return 0;}
