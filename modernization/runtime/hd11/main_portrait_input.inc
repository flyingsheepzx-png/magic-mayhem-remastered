// Main portrait targeting: 0 native fallback, 1 left cast, 2 consumed.
int __cdecl portrait_cast(unsigned flags){
    if(flags&15)reset_spell_double_press();
    if(*reinterpret_cast<int*>(0x6e1f0c)>1 ||
       *reinterpret_cast<int*>(0x6903e8)!=2 || !(flags&15))return 0;
    auto* unit=*reinterpret_cast<unsigned char**>(0x6a2dd0+0x18ec);
    if(!readable(unit,0x5ec) || *reinterpret_cast<int*>(unit+0x5e8)<0)return 0;
    if(flags&12){
        // Swallow right down as well as release: neither may reach native cast.
        if(flags&8){
            typedef void (__thiscall* PendingFn)(void*,int);
            ((PendingFn)0x509bd0)(unit,-1);
        }
        return 2;
    }
    return (flags&2)?1:0;
}
