// Called only from native battle keydown dispatch, after its text-input gate.
int __cdecl roof_tab(unsigned key,unsigned lparam,void* owner){
    if(key!=VK_TAB || *reinterpret_cast<int*>(0x6e1f0c)>1)return 0;
    if((GetKeyState(VK_CONTROL)|GetKeyState(VK_MENU)|GetKeyState(VK_SHIFT))&0x8000)return 0;
    if(!readable(owner,0x100b7) || *reinterpret_cast<int*>(0x689999)<=0)return 0;
    if(*reinterpret_cast<int*>(0x68999d)==0 &&
       !readable(*reinterpret_cast<void**>(0x689955),16))return 0;
    if(!(lparam&(1u<<30))){
        reset_spell_double_press();
        typedef int (__thiscall* RoofFn)(void*,int);
        ((RoofFn)0x46fc50)(owner,0);
    }
    return 1;
}
