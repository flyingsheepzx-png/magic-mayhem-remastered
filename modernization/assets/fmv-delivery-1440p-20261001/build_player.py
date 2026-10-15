"""Compile isolated player and launcher from verified current 1.1 resources."""
import sys,json,shutil,re,subprocess
from pathlib import Path
import pefile
from deliver import ROOT,sha
PROJECT=ROOT.parents[2]
sys.path.insert(0,str(PROJECT/'modernization/tools'))
import compare_remastered_ui_11 as c
VC='C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat'
def main():
 package=c.CANDIDATE
 identity=c.verify_package(package,'1.1',sha(package/'manifest.json'))
 (ROOT/'player-source-identity.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
 lab=ROOT/'playtest'
 if not lab.exists():c.stage(identity,lab)
 else:assert sha(lab/'runtime/Chaos-Wide169-engine.exe')==identity['engine_sha256']
 # Extract exact latest resources; rebuilding older QoL source would drop fixes.
 pe=pefile.PE(str(package/identity['launcher_name']))
 for e in pe.DIRECTORY_ENTRY_RESOURCE.entries:
  if e.id!=10:continue
  for item in e.directory.entries:
   if item.id not in (101,102):continue
   d=item.directory.entries[0].data.struct
   (ROOT/('repath.dll' if item.id==101 else 'qol_bindings.dll')).write_bytes(pe.get_data(d.OffsetToData,d.Size))
 source=(PROJECT/'modernization/build/remastered-1.1-p1/launcher.cpp').read_text(encoding='utf-8')
 for n in ('jpeg.dll','jpeg_native.dll','png_assets.dll','terrain_diagonal.dll','png_pages.dll'):
  pattern=r'(sha256\(game\+L"\\\\'+re.escape(n)+r'",L")[0-9a-f]{64}("\))'
  source,count=re.subn(pattern,lambda m:m[1]+sha(lab/'runtime'/n)+m[2],source);assert count==1,(n,count)
 source=source.replace('FALSE,0,nullptr,game.c_str()', 'FALSE,CREATE_SUSPENDED,nullptr,game.c_str()')
 assert 'FALSE,CREATE_SUSPENDED' in source
 needle='    wchar_t temp[MAX_PATH];'
 enginepe=pefile.PE(str(lab/'runtime/Chaos-Wide169-engine.exe'));entry=enginepe.OPTIONAL_HEADER.ImageBase+enginepe.OPTIONAL_HEADER.AddressOfEntryPoint
 injection='''    void* gate=(void*)ENTRY; BYTE original[2],loop[2]={0xeb,0xfe};SIZE_T count=0;DWORD old;
    if(!ReadProcessMemory(pi.hProcess,gate,original,2,&count)||count!=2 || !VirtualProtectEx(pi.hProcess,gate,2,PAGE_EXECUTE_READWRITE,&old) || !WriteProcessMemory(pi.hProcess,gate,loop,2,&count)) {TerminateProcess(pi.hProcess,1);return 21;}
    FlushInstructionCache(pi.hProcess,gate,2);ResumeThread(pi.hThread);
    SetEnvironmentVariableW(L"MM_FMV_H264",L"1");
    if (!sha256(game+L"\\\\fmv_h264.dll",L"HASH") || !inject(pi,game+L"\\\\fmv_h264.dll")) {TerminateProcess(pi.hProcess,1);return 20;}
    SuspendThread(pi.hThread);
    if(!WriteProcessMemory(pi.hProcess,gate,original,2,&count)||count!=2){TerminateProcess(pi.hProcess,1);return 22;}
    FlushInstructionCache(pi.hProcess,gate,2);DWORD ignored;VirtualProtectEx(pi.hProcess,gate,2,old,&ignored);
    ResumeThread(pi.hThread);
'''.replace('ENTRY',hex(entry))
 # Environment must be set before child creation (not only before injection).
 source=source.replace('    if (!CreateProcessW(', '    SetEnvironmentVariableW(L"MM_FMV_H264",L"1");\n    if (!CreateProcessW(')
 (ROOT/'combined.rc').write_text('101 RCDATA "repath.dll"\n102 RCDATA "qol_bindings.dll"\n')
 cmd='@echo off\ncall "'+VC+'" x86 >nul\nif errorlevel 1 exit /b 1\ncl /nologo /LD /MT /O2 /EHsc /std:c++17 /W4 fmv_h264.cpp /link /OUT:fmv_h264.dll mfplay.lib mfplat.lib mfuuid.lib ole32.lib bcrypt.lib user32.lib gdi32.lib\n'
 cmd+='if errorlevel 1 exit /b 1\ncl /nologo /MT /O2 /EHsc /std:c++17 audio_meter.cpp /link /OUT:audio_meter.exe ole32.lib\n'
 (ROOT/'build-hook.cmd').write_text(cmd)
 subprocess.run(['cmd.exe','/c','build-hook.cmd'],cwd=ROOT,check=True)
 source=source.replace(needle,injection.replace('HASH',sha(ROOT/'fmv_h264.dll'))+needle)
 (ROOT/'launcher.cpp').write_text(source)
 cmd='@echo off\ncall "'+VC+'" x86 >nul\nif errorlevel 1 exit /b 1\nrc /nologo /focandidate.res combined.rc\nif errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:FMV-1440p-Playtest.exe bcrypt.lib user32.lib\n'
 (ROOT/'build-launcher.cmd').write_text(cmd)
 subprocess.run(['cmd.exe','/c','build-launcher.cmd'],cwd=ROOT,check=True)
 shutil.copy2(ROOT/'FMV-1440p-Playtest.exe',lab/'FMV-1440p-Playtest.exe');shutil.copy2(ROOT/'fmv_h264.dll',lab/'runtime/fmv_h264.dll')
 (ROOT/'player-build.json').write_text(json.dumps({'engine_sha256':identity['engine_sha256'],'launcher_sha256':sha(lab/'FMV-1440p-Playtest.exe'),'dll_sha256':sha(ROOT/'fmv_h264.dll'),'shared_runtime_modified':False,'roll_back':'delete no files; use original 1.1 launcher; opt-in separate directory'},indent=2))
 print('BUILT',lab,flush=True)
if __name__=='__main__':main()
