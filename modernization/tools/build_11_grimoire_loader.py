"""Build scoped PNG-first Grimoire loading, preserving native fallback."""
import shutil,subprocess
import build_remastered_11 as b
OUT=b.ROOT/'modernization/build/remastered-1.1-grimoire-load'
def build():
 OUT.mkdir(exist_ok=False)
 text=(b.ROOT/'modernization/runtime/png-pages/png_pages.cpp').read_text(encoding='utf-8')
 old='if(dot!=std::string::npos && !_stricmp(path.c_str()+dot,".BMP"))'
 assert text.count(old)==1
 text=text.replace(old,'if(dot!=std::string::npos && (!_stricmp(path.c_str()+dot,".BMP") || !_stricmp(path.c_str()+dot,".PNG") || !_stricmp(path.c_str()+dot,".JPG")))')
 start=text.index('#ifndef MM_PNG_TEST\nstatic bool install()');end=text.index('#endif\nBOOL WINAPI DllMain',start)
 text=text[:start]+'''#ifndef MM_PNG_TEST
static int __fastcall png_or_jpeg(void* image,void*,const char* filename){
    int result=mm_png_page(image,nullptr,filename);
    if(result)return result;
    using Native=int(__thiscall*)(void*,const char*);
    return reinterpret_cast<Native>(0x58d320)(image,filename);
}
static bool install(){
    if(GetModuleHandleW(nullptr)!=reinterpret_cast<HMODULE>(0x400000))return false;
    struct Call{unsigned site,target;void* hook;};
    Call calls[]={{0x4c532f,0x58d1a0,(void*)mm_png_page},
        {0x4c5380,0x58d320,(void*)png_or_jpeg},
        {0x4c574c,0x58d320,(void*)png_or_jpeg},
        {0x4c575c,0x58d1a0,(void*)mm_png_page}};
    for(auto c:calls){auto* site=(BYTE*)c.site;
        if(site[0]!=0xe8 || c.site+5+*(int32_t*)(site+1)!=c.target)return false;}
    for(auto c:calls){auto* site=(BYTE*)c.site;BYTE replacement[5]={0xe8};
        *(int32_t*)(replacement+1)=static_cast<int32_t>((uintptr_t)c.hook-(c.site+5));
        DWORD old=0,ignored=0;if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
        memcpy(site,replacement,5);FlushInstructionCache(GetCurrentProcess(),site,5);
        VirtualProtect(site,5,old,&ignored);}
    return true;
}
'''+text[end:]
 (b.SRC/'png_grimoire.cpp').write_text(text,encoding='utf-8');(OUT/'png_grimoire.cpp').write_text(text,encoding='utf-8')
 source=b.ROOT/'modernization/build/remastered-1.1-cursor-full'
 for n in ['launcher.cpp','qol_bindings.dll','repath.dll','combined.rc']:shutil.copy2(source/n,OUT/n)
 cmd='@echo off\ncall "'+str(b.VC)+'" x86 >nul\n'
 for define,name in [('', 'png_pages'),('/DMM_PNG_TEST','png_pages_test')]:
  cmd+=f'cl /nologo /LD /MT /O2 /EHsc /std:c++17 /W4 {define} png_grimoire.cpp /link /OUT:{name}.dll ole32.lib windowscodecs.lib gdi32.lib\nif errorlevel 1 exit /b 1\n'
 (OUT/'build-module.cmd').write_text(cmd,encoding='ascii')
 subprocess.run(['cmd','/c','build-module.cmd'],cwd=OUT,check=True)
 launcher=(OUT/'launcher.cpp').read_text(encoding='utf-8')
 previous='bc03168bd19a3e6e376f06a79d6e9fa8fcff3f896c6c23bf0ad60251cb2c9bd7'
 assert launcher.count(previous)==1
 (OUT/'launcher.cpp').write_text(launcher.replace(previous,b.sha(OUT/'png_pages.dll')),encoding='utf-8')
 cmd='@echo off\ncall "'+str(b.VC)+'" x86 >nul\nrc /nologo /focandidate.res combined.rc\nif errorlevel 1 exit /b 1\ncl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:MagicMayhem-Remastered-1.1.exe bcrypt.lib user32.lib\n'
 (OUT/'build-launcher.cmd').write_text(cmd,encoding='ascii');subprocess.run(['cmd','/c','build-launcher.cmd'],cwd=OUT,check=True)
 b.write(OUT/'build.json',dict(png_sha256=b.sha(OUT/'png_pages.dll'),launcher_sha256=b.sha(OUT/'MagicMayhem-Remastered-1.1.exe')))
if __name__=='__main__':build()
