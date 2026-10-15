"""Selective map adaptation on latest QoL, preserving all other features."""
def adapt(q):
    def once(a,b):
        nonlocal q
        if q.count(a)!=1:raise RuntimeError('Realm source signature mismatch: '+a[:90])
        q=q.replace(a,b,1)
    once('void __cdecl project_realm_point(int* x,int* y){',        'bool realm_projection_enabled(){\n    int w=*reinterpret_cast<int*>(0x6a49f0),h=*reinterpret_cast<int*>(0x6a49f4);\n    return (w==1280 && h==720) || (w==2560 && h==1440);\n}\nMmUiViewport realm_viewport(){return mm_ui_fit(*reinterpret_cast<int*>(0x6a49f0),*reinterpret_cast<int*>(0x6a49f4));}\nint __cdecl realm_content_x(int x){return x-realm_viewport().x;}\nvoid __cdecl project_realm_point(int* x,int* y){')
    once('    if(*reinterpret_cast<int*>(0x6a49f0)!=1280 ||\n       *reinterpret_cast<int*>(0x6a49f4)!=720)return;\n    *x=(*x*6+2)/5+160;\n    *y=(*y*6+2)/5;',         '    if(!realm_projection_enabled())return;\n    MmUiViewport v=realm_viewport();\n    *x=mm_ui_project_x(v,*x);*y=mm_ui_project_y(v,*y);')
    # Native mask sampler already uses scaled denominators. Remove only origin;
    # applying inverse scale here as well would transform mouse input twice.
    once('    sub esi,160\n    jmp dword ptr [realm_hover_resume]',         '    pushfd\n    pushad\n    push esi\n    call realm_content_x\n    add esp,4\n    mov [esp+4],eax\n    popad\n    popfd\n    jmp dword ptr [realm_hover_resume]')
    once('    if(source!=realm_highlight_source || *reinterpret_cast<int*>(0x6a49f0)!=1280 ||\n       *reinterpret_cast<int*>(0x6a49f4)!=720)return 0;',         '    if(source!=realm_highlight_source || !realm_projection_enabled())return 0;')
    q=q.replace('same 6/5 scale.','same viewport scale.').replace('underlying 960x720 map.','underlying fitted map canvas.')
    return '#include "ui_geometry.h"\n'+q
