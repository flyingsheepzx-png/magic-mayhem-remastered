// Hash-gated main entry for the frozen single-player 30/60 candidate.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <bcrypt.h>
#include <string>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

#ifndef MM_EXPECTED_ENGINE_SHA
#define MM_EXPECTED_ENGINE_SHA L"42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da"
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

// Exact argument, never forwarded to the engine. Ordinary startup always clears
// inherited diagnostic flags. Snapshot BEFORE CreateProcess starts native learning.
static bool prepare_ai_trace(const std::wstring& game,LPWSTR arguments,std::wstring& directory) {
    SetEnvironmentVariableW(L"MM_AI_TRACE",nullptr);
    SetEnvironmentVariableW(L"MM_AI_TRACE_DIR",nullptr);
    std::wstring value=arguments?arguments:L"";
    size_t first=value.find_first_not_of(L" \t"),last=value.find_last_not_of(L" \t");
    if(first==std::wstring::npos || value.substr(first,last-first+1)!=L"--ai-trace")return true;
    CreateDirectoryW((game+L"\\AI\\diagnostics").c_str(),nullptr);
    directory=game+L"\\AI\\diagnostics\\session-"+std::to_wstring(GetCurrentProcessId())+L"-"+std::to_wstring(GetTickCount());
    if(!CreateDirectoryW(directory.c_str(),nullptr))return false;
    const wchar_t* files[]={L"AI\\Brain.dat",L"AI\\EXPERIEN.DAT",L"CFG\\ai.cfg",L"CFG\\chaos.cfg",L"CFG\\prefs.cfg",L"CFG\\creature.cfg"};
    for(auto file:files) {
        std::wstring source=game+L"\\"+file;
        std::wstring dest=directory+L"\\"+source.substr(source.find_last_of(L"\\")+1);
        if(!CopyFileW(source.c_str(),dest.c_str(),TRUE))return false;
    }
    SetEnvironmentVariableW(L"MM_AI_TRACE",L"1");
    SetEnvironmentVariableW(L"MM_AI_TRACE_DIR",directory.c_str());
    return true;
}

int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR arguments,int) {
    wchar_t module[MAX_PATH];
    if (!GetModuleFileNameW(instance,module,MAX_PATH)) {fail(L"Cannot locate launcher.");return 1;}
#ifdef MM_INSTALLED_LAUNCHER
    std::wstring game=parent(module)+L"\\runtime";
#else
    std::wstring game=parent(parent(parent(module)));
#endif
    if (!sha256(game+L"\\jpeg.dll",L"17b60b30e80685567e5b07abee2f7c6def70c8f3af99e31f564aa6fca175ad64") || !sha256(game+L"\\jpeg_native.dll",L"a8c2480789bb45ab6ff2d1779e0e7d454b35290f89b20fa3c999a9c0c263328b") || !sha256(game+L"\\png_assets.dll",L"48916f6cc6ffd183e0c2ee90caf6d1571a28e627e36197747ec9e96d3772b427")) {fail(L"PNG asset runtime identity mismatch. No game was started.");return 13;}
    std::wstring exe=game+L"\\Chaos-Wide169-engine.exe";
    const wchar_t* expected=MM_EXPECTED_ENGINE_SHA;
    if (!sha256(exe,expected)) {fail(L"Unknown or missing single-player executable. No game changes were made.");return 2;}
    if (game_running()) {fail(L"Close the running game before starting another copy.");return 3;}
    std::wstring ai_directory;
    if(!prepare_ai_trace(game,arguments,ai_directory)){fail(L"AI diagnostic snapshot could not be prepared.");return 24;}
    HRSRC resource=FindResourceW(instance,MAKEINTRESOURCEW(101),MAKEINTRESOURCEW(10));
    HRSRC qol_resource=FindResourceW(instance,MAKEINTRESOURCEW(102),MAKEINTRESOURCEW(10));
    if (!resource || !qol_resource) {fail(L"Game modules are missing from the launcher.");return 4;}
    HGLOBAL loaded=LoadResource(instance,resource);
    const void* data=LockResource(loaded);DWORD size=SizeofResource(instance,resource);
    HGLOBAL qol_loaded=LoadResource(instance,qol_resource);
    const void* qol_data=LockResource(qol_loaded);DWORD qol_size=SizeofResource(instance,qol_resource);
    if (!data || !size || !qol_data || !qol_size) {fail(L"Game modules could not be read.");return 5;}
    const wchar_t* diagnostic_flags[]={L"MM_PROBE_BACKGROUND_INPUT",L"MM_PROBE_TRACE",L"MM_PROBE_FRAME_HASH",L"MM_PROBE_SURFACE_CALLS",L"MM_REALM_HIGHLIGHT_TRACE"};
    for(auto flag:diagnostic_flags)SetEnvironmentVariableW(flag,nullptr);
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
    SetEnvironmentVariableW(L"MM_PROBE_MIXED_RENDER",L"1");
    SetEnvironmentVariableW(L"MM_PROBE_MIXED_FONTS",L"1");
    SetEnvironmentVariableW(L"MM_PROBE_BATTLE_SHARPEN",L"0");
    SetEnvironmentVariableW(L"MM_FMV_H264",L"1");
    if (!CreateProcessW(exe.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_SUSPENDED,nullptr,game.c_str(),&startup,&pi)) {
        fail(L"The game could not be started.");return 6;
    }
    void* gate=(void*)0x5c4090; BYTE original[2],loop[2]={0xeb,0xfe};SIZE_T count=0;DWORD old;
    if(!ReadProcessMemory(pi.hProcess,gate,original,2,&count)||count!=2 || !VirtualProtectEx(pi.hProcess,gate,2,PAGE_EXECUTE_READWRITE,&old) || !WriteProcessMemory(pi.hProcess,gate,loop,2,&count)) {TerminateProcess(pi.hProcess,1);return 21;}
    FlushInstructionCache(pi.hProcess,gate,2);ResumeThread(pi.hThread);
    SetEnvironmentVariableW(L"MM_FMV_H264",L"1");
    if (!sha256(game+L"\\fmv_h264.dll",L"9b86df83d71198afe02474fbeae5380f55da99746cc051e6ac169d9263108789") || !inject(pi,game+L"\\fmv_h264.dll")) {TerminateProcess(pi.hProcess,1);return 20;}
    SuspendThread(pi.hThread);
    if(!WriteProcessMemory(pi.hProcess,gate,original,2,&count)||count!=2){TerminateProcess(pi.hProcess,1);return 22;}
    FlushInstructionCache(pi.hProcess,gate,2);DWORD ignored;VirtualProtectEx(pi.hProcess,gate,2,old,&ignored);
    ResumeThread(pi.hThread);
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
    if (!sha256(game+L"\\terrain_diagonal.dll",L"3a27cafa8a0f282b6bade57e3fee4e8d89511191f2d1b9aea1852399d3ca66d3") || !inject(pi,game+L"\\terrain_diagonal.dll")) {
        TerminateProcess(pi.hProcess,1);fail(L"Terrain module failed.");return 11;
    }
    if (!sha256(game+L"\\png_pages.dll",L"a48ae4e039114993f2a65a442d07b147ba6794bb725b1e740218d7d7735f6d7e") || !inject(pi,game+L"\\png_pages.dll")) {
        TerminateProcess(pi.hProcess,1);WaitForSingleObject(pi.hProcess,5000);
        DeleteFileW(qol.c_str());DeleteFileW(dll.c_str());
        CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
        fail(L"PNG page module failed. No unmodified run is allowed.");return 12;
    }

    std::wstring ai;
    if(!ai_directory.empty()) {
        HRSRC ai_resource=FindResourceW(instance,MAKEINTRESOURCEW(103),MAKEINTRESOURCEW(10));
        HGLOBAL ai_loaded=ai_resource?LoadResource(instance,ai_resource):nullptr;
        const void* ai_data=ai_loaded?LockResource(ai_loaded):nullptr;
        DWORD ai_size=ai_resource?SizeofResource(instance,ai_resource):0;
        ai=std::wstring(temp)+L"mm-ai-"+std::to_wstring(pi.dwProcessId)+L".dll";
        HANDLE ai_output=CreateFileW(ai.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);
        DWORD ai_written=0;
        bool ai_saved=ai_output!=INVALID_HANDLE_VALUE && ai_data && ai_size &&
            WriteFile(ai_output,ai_data,ai_size,&ai_written,nullptr) && ai_written==ai_size;
        if(ai_output!=INVALID_HANDLE_VALUE)CloseHandle(ai_output);
        if(!ai_saved || !inject(pi,ai)) {
            TerminateProcess(pi.hProcess,1);WaitForSingleObject(pi.hProcess,5000);
            DeleteFileW(ai.c_str());DeleteFileW(qol.c_str());DeleteFileW(dll.c_str());
            CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
            fail(L"AI diagnostics could not initialize. No diagnostic gameplay was started.");return 23;
        }
    }

    CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess,INFINITE);
    CloseHandle(pi.hProcess);
    if(!ai.empty())for(int i=0;i<20 && !DeleteFileW(ai.c_str());i++)Sleep(100);
    for (int i=0;i<20 && !DeleteFileW(dll.c_str());i++) Sleep(100);
    for (int i=0;i<20 && !DeleteFileW(qol.c_str());i++) Sleep(100);
    return 0;
}
