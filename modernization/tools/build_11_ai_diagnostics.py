"""Embed opt-in AI telemetry while retaining exact current 101/102 modules."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import build_remastered_11 as b
import build_11_surface_lifecycle as base
from install_11_minimap_v2 import resources
from build_11_fmv_h264 import replace

OUT=b.ROOT/'modernization/build/remastered-1.1-ai-diagnostics'
BACK=b.ROOT/'modernization/backups/remastered-1.1-ai-diagnostics'
SOURCE=b.ROOT/'modernization/build/remastered-1.1-occlusion-opacity'
ENGINE='42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da'
MODULES={101:'a680f98e3b51f8f8e315fe52af5055b6fdc3d1586d19a4ae3d9b598d201264b8',
         102:'1b4b1d36d10c11bc4c491f60670947310d8165c3532f038484884dfc4e6b6a21'}

LAUNCH_HELPER=r'''
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
'''
INJECT=r'''
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
'''

def build():
    rows=[]
    for entry,manifest,kind in base.targets():
        m=json.loads(manifest.read_text(encoding='utf-8'))
        assert b.sha(entry)==m['launcher_sha256']
        assert b.sha(entry.parent/'runtime/Chaos-Wide169-engine.exe')==m['engine_sha256']==ENGINE
        r=resources(entry)
        for key,sha in MODULES.items():assert hashlib.sha256(r[key]).hexdigest()==sha
        rows.append(dict(entry=str(entry),manifest=str(manifest),kind=kind,
                         entry_sha256=b.sha(entry),manifest_sha256=b.sha(manifest)))
    OUT.mkdir(exist_ok=False)
    current=resources(base.targets()[0][0])
    for key,name in [(101,'repath.dll'),(102,'qol_bindings.dll')]:
        (OUT/name).write_bytes(current[key])
    shutil.copy2(b.ROOT/'modernization/runtime/hd11/ai_diagnostics.cpp',OUT/'ai_diagnostics.cpp')
    shutil.copy2(SOURCE/'remastered.ico',OUT/'remastered.ico')
    for name in ['launcher.cpp','release_launcher.cpp']:
        s=(SOURCE/name).read_text(encoding='utf-8')
        s=b.replace_once(s,'int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR,int) {',
                         LAUNCH_HELPER+'\nint WINAPI wWinMain(HINSTANCE instance,HINSTANCE,LPWSTR arguments,int) {')
        needle='    HRSRC resource=FindResourceW(instance,MAKEINTRESOURCEW(101),MAKEINTRESOURCEW(10));'
        s=b.replace_once(s,needle,'    std::wstring ai_directory;\n    if(!prepare_ai_trace(game,arguments,ai_directory)){fail(L"AI diagnostic snapshot could not be prepared.");return 24;}\n'+needle)
        s=b.replace_once(s,'    CloseHandle(pi.hThread);\n    WaitForSingleObject(pi.hProcess,INFINITE);',
                         INJECT+'\n    CloseHandle(pi.hThread);\n    WaitForSingleObject(pi.hProcess,INFINITE);')
        s=b.replace_once(s,'    for (int i=0;i<20 && !DeleteFileW(dll.c_str());i++) Sleep(100);',
                         '    if(!ai.empty())for(int i=0;i<20 && !DeleteFileW(ai.c_str());i++)Sleep(100);\n    for (int i=0;i<20 && !DeleteFileW(dll.c_str());i++) Sleep(100);')
        (OUT/name).write_text(s,encoding='utf-8')
    for name in ['candidate','release']:
        (OUT/(name+'.rc')).write_text(('1 ICON "remastered.ico"\n' if name=='release' else '')+
             '101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n103 RCDATA "ai_diagnostics.dll"\n')
    cmd=(SOURCE/'build.cmd').read_text()
    begin=cmd.index('cl /nologo /LD');end=cmd.index('rc /nologo',begin)
    cmd=cmd[:begin]+'''cl /nologo /LD /O2 /EHsc /std:c++17 /W4 ai_diagnostics.cpp /link /OUT:ai_diagnostics.dll /MAP:ai_diagnostics.map bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
'''+cmd[end:]
    (OUT/'build.cmd').write_text(cmd)
    subprocess.run(['cmd','/c','build.cmd'],cwd=OUT,check=True)
    base.write(OUT/'before.json',rows)
    verify()

def verify():
    for name in ['candidate.exe','release.exe']:
        r=resources(OUT/name)
        for key,sha in MODULES.items():assert hashlib.sha256(r[key]).hexdigest()==sha
        assert r[103]==(OUT/'ai_diagnostics.dll').read_bytes()
    import verify_11_ai_diagnostics as v
    result=v.verify(OUT)
    result.update(result='passed',module_sha256=b.sha(OUT/'ai_diagnostics.dll'),
                  retained_modules={str(k):v for k,v in MODULES.items()},default_enabled=False,
                  runtime_acceptance='pending user diagnostic gameplay; no gameplay launched')
    base.write(OUT/'verification.json',result)

def install():
    base.idle()
    v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
    assert v['result']=='passed' and v['module_sha256']==b.sha(OUT/'ai_diagnostics.dll')
    for row in json.loads((OUT/'before.json').read_text(encoding='utf-8')):
        assert b.sha(Path(row['entry']))==row['entry_sha256'] and b.sha(Path(row['manifest']))==row['manifest_sha256']
    BACK.mkdir(exist_ok=False);changes=[]
    for i,row in enumerate(json.loads((OUT/'before.json').read_text(encoding='utf-8'))):
        entry,manifest=Path(row['entry']),Path(row['manifest'])
        new=OUT/('candidate.exe' if row['kind']=='candidate' else 'release.exe')
        m=json.loads(manifest.read_text(encoding='utf-8'));m['launcher_sha256']=b.sha(new)
        m['ai_diagnostics']=v
        if row['kind']=='release':
            m['files'][entry.name]=b.sha(new);m['embedded_modules']['103']=b.sha(OUT/'ai_diagnostics.dll')
        for j,(p,data) in enumerate([(entry,new.read_bytes()),(manifest,(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode())]):
            backup=BACK/f'{i}-{j}.bak';backup.write_bytes(p.read_bytes())
            changes.append(dict(path=str(p),backup=str(backup),before_sha256=b.sha(p),
                                after_sha256=hashlib.sha256(data).hexdigest(),data=data))
    base.write(BACK/'rollback.json',[{k:v for k,v in r.items() if k!='data'} for r in changes])
    try:
        for r in changes:replace(Path(r['path']),r['data']);assert b.sha(Path(r['path']))==r['after_sha256']
    except BaseException:
        for r in changes:replace(Path(r['path']),Path(r['backup']).read_bytes())
        raise
    print('Installed optional AI diagnostics; ordinary launch disabled; user gameplay pending')

def rollback():
    base.OUT=OUT;base.BACK=BACK;base.rollback()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify','install','rollback'])
    globals()[p.parse_args().action]()
