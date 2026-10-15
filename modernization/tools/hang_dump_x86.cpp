// Read-only dump helper. Caller verifies engine hash; repeat PID/path gate here.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dbghelp.h>
#include <cstdio>
#include <cstdlib>
int wmain(int argc,wchar_t** argv){
 if(argc!=4)return 2;
 DWORD pid=wcstoul(argv[1],nullptr,10);
 HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ,FALSE,pid);
 if(!process){wprintf(L"OpenProcess error %lu\n",GetLastError());return 3;}
 wchar_t path[32768];DWORD size=32768;
 if(!QueryFullProcessImageNameW(process,0,path,&size)||_wcsicmp(path,argv[2])){CloseHandle(process);return 4;}
 HANDLE file=CreateFileW(argv[3],GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(file==INVALID_HANDLE_VALUE){CloseHandle(process);return 5;}
 BOOL ok=MiniDumpWriteDump(process,pid,file,(MINIDUMP_TYPE)0x1820,nullptr,nullptr,nullptr);
 DWORD error=ok?0:GetLastError();CloseHandle(file);CloseHandle(process);
 wprintf(L"MiniDumpWriteDump error %lu\n",error);return ok?0:6;
}
