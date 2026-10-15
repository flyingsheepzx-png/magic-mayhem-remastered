// User-authorized debugger attachment: capture, preserve exception semantics,
// detach on deadline/stop. Never change memory or terminate the target.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dbghelp.h>
#include <cstdio>
#include <string>
#include <cstdlib>
static volatile LONG stop=0;
static BOOL WINAPI control(DWORD){InterlockedExchange(&stop,1);return TRUE;}
int wmain(int argc,wchar_t** argv){
 if(argc!=5)return 2;
 DWORD pid=wcstoul(argv[1],nullptr,10);
 HANDLE process=OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ,FALSE,pid);
 if(!process)return 3;
 wchar_t path[32768];DWORD length=32768;
 if(!QueryFullProcessImageNameW(process,0,path,&length)||_wcsicmp(path,argv[2])){CloseHandle(process);return 4;}
 std::wstring folder=argv[3];DWORD seconds=wcstoul(argv[4],nullptr,10);
 if(seconds<1||seconds>1800){CloseHandle(process);return 5;}
 FILE* log=nullptr;_wfopen_s(&log,(folder+L"\\events.jsonl").c_str(),L"ab");if(!log){CloseHandle(process);return 6;}
 if(!DebugActiveProcess(pid)){fprintf(log,"{\"attach_error\":%lu}\n",GetLastError());fclose(log);CloseHandle(process);return 7;}
 if(!DebugSetProcessKillOnExit(FALSE)){DebugActiveProcessStop(pid);fclose(log);CloseHandle(process);return 8;}
 SetConsoleCtrlHandler(control,TRUE);
 fprintf(log,"{\"attached_pid\":%lu,\"seconds\":%lu,\"kill_on_exit\":false}\n",pid,seconds);fflush(log);
 printf("ATTACHED PID %lu; capture armed; deadline %lu seconds\n",pid,seconds);fflush(stdout);
 ULONGLONG deadline=GetTickCount64()+seconds*1000ULL;bool initial_break=true,exited=false;unsigned avs=0;
 while(!stop&&GetTickCount64()<deadline){
  if(GetFileAttributesW((folder+L"\\stop.capture").c_str())!=INVALID_FILE_ATTRIBUTES)break;
  DEBUG_EVENT event{};
  if(!WaitForDebugEvent(&event,250)){if(GetLastError()==ERROR_SEM_TIMEOUT)continue;break;}
  DWORD status=DBG_CONTINUE;
  if(event.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT){
   if(event.u.CreateProcessInfo.hFile)CloseHandle(event.u.CreateProcessInfo.hFile);
   if(event.u.CreateProcessInfo.hThread)CloseHandle(event.u.CreateProcessInfo.hThread);
   if(event.u.CreateProcessInfo.hProcess)CloseHandle(event.u.CreateProcessInfo.hProcess);
  }else if(event.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT){
   if(event.u.CreateThread.hThread)CloseHandle(event.u.CreateThread.hThread);
  }else if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT){
   if(event.u.LoadDll.hFile)CloseHandle(event.u.LoadDll.hFile);
  }else if(event.dwDebugEventCode==EXCEPTION_DEBUG_EVENT){
   auto& exception=event.u.Exception;DWORD code=exception.ExceptionRecord.ExceptionCode;
   status=DBG_EXCEPTION_NOT_HANDLED;
   if(code==EXCEPTION_BREAKPOINT&&initial_break){status=DBG_CONTINUE;initial_break=false;}
   fprintf(log,"{\"exception\":\"0x%08lx\",\"address\":\"0x%p\",\"first_chance\":%lu,\"tid\":%lu,\"tick\":%llu}\n",code,exception.ExceptionRecord.ExceptionAddress,exception.dwFirstChance,event.dwThreadId,GetTickCount64());fflush(log);
   if(code==EXCEPTION_ACCESS_VIOLATION&&avs<8){
    ++avs;HANDLE thread=OpenThread(THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId);
    CONTEXT ctx{};ctx.ContextFlags=CONTEXT_FULL;
    BOOL context_ok=thread&&GetThreadContext(thread,&ctx);
    if(thread)CloseHandle(thread);
    fprintf(log,"{\"av\":%u,\"context_ok\":%d,\"eip\":\"0x%08lx\",\"esp\":\"0x%08lx\",\"ebp\":\"0x%08lx\",\"eax\":\"0x%08lx\",\"ebx\":\"0x%08lx\",\"ecx\":\"0x%08lx\",\"edx\":\"0x%08lx\",\"esi\":\"0x%08lx\",\"edi\":\"0x%08lx\",\"access\":%lu,\"fault\":\"0x%08lx\"}\n",avs,context_ok,ctx.Eip,ctx.Esp,ctx.Ebp,ctx.Eax,ctx.Ebx,ctx.Ecx,ctx.Edx,ctx.Esi,ctx.Edi,(DWORD)exception.ExceptionRecord.ExceptionInformation[0],(DWORD)exception.ExceptionRecord.ExceptionInformation[1]);fflush(log);
    std::wstring filename=folder+L"\\av-"+std::to_wstring(avs)+L".dmp";
    HANDLE file=CreateFileW(filename.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    BOOL dumped=FALSE;DWORD error=0;
    if(file!=INVALID_HANDLE_VALUE){
     EXCEPTION_POINTERS pointers{&exception.ExceptionRecord,&ctx};
     MINIDUMP_EXCEPTION_INFORMATION info{event.dwThreadId,&pointers,FALSE};
     dumped=MiniDumpWriteDump(process,pid,file,(MINIDUMP_TYPE)(avs==1?0x1822:0x1820),context_ok?&info:nullptr,nullptr,nullptr);
     error=dumped?0:GetLastError();CloseHandle(file);
    }else error=GetLastError();
    fprintf(log,"{\"dump\":%u,\"success\":%d,\"error\":%lu}\n",avs,dumped,error);fflush(log);
    printf("CAPTURED AV %u EIP %08lx fault %08lx dump=%d error=%lu\n",avs,ctx.Eip,(DWORD)exception.ExceptionRecord.ExceptionInformation[1],dumped,error);fflush(stdout);
   }
  }else if(event.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT){
   fprintf(log,"{\"exit_code\":%lu}\n",event.u.ExitProcess.dwExitCode);fflush(log);exited=true;
  }
  if(!ContinueDebugEvent(event.dwProcessId,event.dwThreadId,status)){fprintf(log,"{\"continue_error\":%lu}\n",GetLastError());fflush(log);break;}
  if(exited)break;
 }
 BOOL detached=exited?TRUE:DebugActiveProcessStop(pid);
 fprintf(log,"{\"detached\":%d,\"exited\":%d,\"captured_avs\":%u}\n",detached,exited,avs);fclose(log);CloseHandle(process);
 printf("DETACHED=%d captured=%u\n",detached,avs);return detached?0:9;
}
