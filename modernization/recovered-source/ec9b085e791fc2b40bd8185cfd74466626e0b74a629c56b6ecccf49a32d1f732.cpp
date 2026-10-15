// Hash-gated main entry for the frozen single-player 30/60 candidate.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <bcrypt.h>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

#ifndef MM_EXPECTED_ENGINE_SHA
#define MM_EXPECTED_ENGINE_SHA L"43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d"
#endif

static std::wstring parent(const std::wstring& path) {
    size_t i=path.find_last_of(L"\\/");
    return i==std::wstring::npos?L"":path.substr(0,i);
}
static void fail(const wchar_t* message) {
#ifdef MM_INSTALLED_LAUNCHER
    MessageBoxW(nullptr,message,L"Magic & Mayhem",MB_ICONERROR|MB_OK);
#else
    MessageBoxW(nullptr,message,L"Magic & Mayhem reroute diagnostic",MB_ICONERROR|MB_OK);
#endif
}
static bool sha256(const std::wstring& path,const wchar_t* expected) {
    HANDLE file=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if (file==INVALID_HANDLE_VALUE) return false;
    BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    DWORD object_size=0,result_size=0;bool okay=false;
    std::vector<unsigned char> object;
    unsigned char digest[32]={};
    if (BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)!=0) goto done;
    if (BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&object_size,sizeof(object_size),&result_size,0)!=0) goto done;
    object.resize(object_size);
    if (BCryptCreateHash(alg,&hash,object.data(),object_size,nullptr,0,0)!=0) goto done;
    unsigned char block[65536];DWORD count;
    while (ReadFile(file,block,sizeof(block),&count,nullptr) && count) {
        if (BCryptHashData(hash,block,count,0)!=0) goto done;
    }
    if (GetLastError()!=ERROR_SUCCESS && count!=0) goto done;
    if (BCryptFinishHash(hash,digest,sizeof(digest),0)!=0) goto done;
    {
        wchar_t actual[65];const wchar_t* digits=L"0123456789abcdef";
        for (int i=0;i<32;i++) {actual[2*i]=digits[digest[i]>>4];actual[2*i+1]=digits[digest[i]&15];}
        actual[64]=0;okay=lstrcmpiW(actual,expected)==0;
    }
done:
    if (hash) BCryptDestroyHash(hash);
    if (alg) BCryptCloseAlgorithmProvider(alg,0);
    CloseHandle(file);return okay;
}
static bool game_running() {
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
    if (snap==INVALID_HANDLE_VALUE) return true;
    PROCESSENTRY32W item={};item.dwSize=sizeof(item);
    bool found=false;
    if (Process32FirstW(snap,&item)) do {
        if (item.th32ProcessID != GetCurrentProcessId() &&
            (!lstrcmpiW(item.szExeFile,L"Chaos.exe") ||
             !lstrcmpiW(item.szExeFile,L"Chaos-Wide169-engine.exe"))) {found=true;break;}
    } while (Process32NextW(snap,&item));
    CloseHandle(snap);return found;
}
static void* remote_load_library(DWORD pid) {
    HMODULE local=GetModuleHandleW(L"kernel32.dll");
    FARPROC routine=GetProcAddress(local,"LoadLibraryW");
    if (!local || !routine) return nullptr;
    for (int attempt=0;attempt<20;attempt++) {
        HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,pid);
        if (snap!=INVALID_HANDLE_VALUE) {
            MODULEENTRY32W item={};item.dwSize=sizeof(item);
            if (Module32FirstW(snap,&item)) do {
                if (!lstrcmpiW(item.szModule,L"kernel32.dll")) {
                    void* address=item.modBaseAddr+((char*)routine-(char*)local);
                    CloseHandle(snap);return address;
                }
            } while (Module32NextW(snap,&item));
            CloseHandle(snap);
        }
        Sleep(100);
    }
    return nullptr;
}
static bool inject(PROCESS_INFORMATION& pi,const std::wstring& dll) {
    void* loader=remote_load_library(pi.dwProcessId);
    if (!loader) return false;
    SIZE_T bytes=(dll.size()+1)*sizeof(wchar_t),written=0;
    void* remote=VirtualAllocEx(pi.hProcess,nullptr,bytes,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    if (!remote) return false;
    bool okay=false;
    if (WriteProcessMemory(pi.hProcess,remote,dll.c_str(),bytes,&written) && written==bytes) {
        HANDLE thread=CreateRemoteThread(pi.hProcess,nullptr,0,(LPTHREAD_START_ROUTINE)loader,remote,0,nullptr);
        if (thread) {
            if (WaitForSingleObject(thread,10000)==WAIT_OBJECT_0) {
                DWORD loaded=0;
                okay=GetExitCodeThread(thread,&loaded) && loaded!=0;
            }
            CloseHandle(thread);
        }
    }
    VirtualFreeEx(pi.hProcess,remote,0,MEM_RELEASE);
    return okay;
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR,int) {
    wchar_t module[MAX_PATH];
    if (!GetModuleFileNameW(instance,module,MAX_PATH)) {fail(L"Cannot locate launcher.");return 1;}
#ifdef MM_INSTALLED_LAUNCHER
    std::wstring game=parent(module);
#else
    std::wstring game=parent(parent(parent(module)));
#endif
    std::wstring exe=game+L"\\Chaos-Wide169-engine.exe";
    const wchar_t* expected=MM_EXPECTED_ENGINE_SHA;
    if (!sha256(exe,expected)) {fail(L"Unknown or missing single-player executable. No game changes were made.");return 2;}
    if (game_running()) {fail(L"Close the running game before starting another copy.");return 3;}
    HRSRC resource=FindResourceW(instance,MAKEINTRESOURCEW(101),MAKEINTRESOURCEW(10));
    HRSRC qol_resource=FindResourceW(instance,MAKEINTRESOURCEW(102),MAKEINTRESOURCEW(10));
    if (!resource || !qol_resource) {fail(L"Game modules are missing from the launcher.");return 4;}
    HGLOBAL loaded=LoadResource(instance,resource);
    const void* data=LockResource(loaded);DWORD size=SizeofResource(instance,resource);
    HGLOBAL qol_loaded=LoadResource(instance,qol_resource);
    const void* qol_data=LockResource(qol_loaded);DWORD qol_size=SizeofResource(instance,qol_resource);
    if (!data || !size || !qol_data || !qol_size) {fail(L"Game modules could not be read.");return 5;}
    STARTUPINFOW startup={};startup.cb=sizeof(startup);
    PROCESS_INFORMATION pi={};
    std::wstring command=L"\""+exe+L"\"";
    // The standalone launcher is safe for ordinary mouse testing; mid-edge
    // interruption is reserved for the controlled background harness.
#ifdef MM_ANIMATION_MOTION_LAUNCHER
    SetEnvironmentVariableW(L"MM_PROBE_ENABLE_REDIRECT",L"1");
    SetEnvironmentVariableW(L"MM_PROBE_ANIMATION_MOTION",L"1");
#else
    SetEnvironmentVariableW(L"MM_PROBE_ENABLE_REDIRECT",L"0");
    SetEnvironmentVariableW(L"MM_PROBE_ANIMATION_MOTION",L"0");
#endif
#ifdef MM_LAYER_LAUNCHER
    SetEnvironmentVariableW(L"MM_PROBE_LAYER_REDIRECT",L"1");
#else
    SetEnvironmentVariableW(L"MM_PROBE_LAYER_REDIRECT",L"0");
#endif
#ifdef MM_FULL_TRIAL_LAUNCHER
    SetEnvironmentVariableW(L"MM_PROBE_RENDER_REPLAY",L"1");
    SetEnvironmentVariableW(L"MM_PROBE_RENDER_CONTINUOUS",L"1");
    SetEnvironmentVariableW(L"MM_PROBE_ORIGINAL_WALLTIME",L"1");
#endif
    if (!CreateProcessW(exe.c_str(),command.data(),nullptr,nullptr,FALSE,0,nullptr,game.c_str(),&startup,&pi)) {
        fail(L"The game could not be started.");return 6;
    }
    wchar_t temp[MAX_PATH];
    if (!GetTempPathW(MAX_PATH,temp)) {TerminateProcess(pi.hProcess,1);fail(L"Temp folder unavailable.");return 7;}
    std::wstring dll=std::wstring(temp)+L"mm-repath-"+std::to_wstring(pi.dwProcessId)+L".dll";
    HANDLE output=CreateFileW(dll.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);
    DWORD written=0;
    bool saved=output!=INVALID_HANDLE_VALUE && WriteFile(output,data,size,&written,nullptr) && written==size;
    if (output!=INVALID_HANDLE_VALUE) CloseHandle(output);
    if (!saved) {
        TerminateProcess(pi.hProcess,1);fail(L"Game module could not be prepared.");
        CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 8;
    }
    WaitForInputIdle(pi.hProcess,10000);
    if (WaitForSingleObject(pi.hProcess,0)==WAIT_OBJECT_0 || !inject(pi,dll)) {
        TerminateProcess(pi.hProcess,1);
        fail(L"Game module could not be loaded. The game was closed to avoid an unmodified run.");
        WaitForSingleObject(pi.hProcess,5000);
        DeleteFileW(dll.c_str());CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 9;
    }
    std::wstring qol=std::wstring(temp)+L"mm-qol-"+std::to_wstring(pi.dwProcessId)+L".dll";
    HANDLE qol_output=CreateFileW(qol.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);
    DWORD qol_written=0;
    bool qol_saved=qol_output!=INVALID_HANDLE_VALUE &&
                   WriteFile(qol_output,qol_data,qol_size,&qol_written,nullptr) && qol_written==qol_size;
    if(qol_output!=INVALID_HANDLE_VALUE)CloseHandle(qol_output);
    if(!qol_saved || !inject(pi,qol)){
        TerminateProcess(pi.hProcess,1);
        fail(L"QoL module could not be loaded. The game was closed.");
        WaitForSingleObject(pi.hProcess,5000);
        DeleteFileW(qol.c_str());DeleteFileW(dll.c_str());
        CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 10;
    }
    if (!sha256(game+L"\\terrain_diagonal.dll",L"3791b8eabf83428b43c21d95d44d43996fd1f2275fbd1b882c803c4fa456ad41") || !inject(pi,game+L"\\terrain_diagonal.dll")) {
        TerminateProcess(pi.hProcess,1);fail(L"Terrain module failed.");return 11;
    }
    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess,INFINITE);
    CloseHandle(pi.hProcess);
    for (int i=0;i<20 && !DeleteFileW(dll.c_str());i++) Sleep(100);
    for (int i=0;i<20 && !DeleteFileW(qol.c_str());i++) Sleep(100);
    return 0;
}
