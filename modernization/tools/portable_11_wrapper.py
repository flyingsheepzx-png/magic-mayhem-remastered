"""Replace the current production compositor's path gate with engine identity."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def apply(ws):
    p=ws/'src/mm_mixed.h';s=p.read_text(encoding='utf-8')
    start=s.index('BOOL mm_mixed_enabled(void)\n{');end=s.index('\n/* The engine keeps pixels',start)
    s=s[:start]+'''BOOL mm_mixed_enabled(void)
{
    static LONG state;
    LONG value=InterlockedExchangeAdd(&state,0);
    if(!value){
        char flag[4]={0};
        GetEnvironmentVariableA("MM_PROBE_MIXED_RENDER",flag,sizeof(flag));
        value=flag[0]=='1' && flag[1]==0 && mm_hd11_current_engine()?2:1;
        InterlockedExchange(&state,value);
    }
    return value==2;
}
'''+s[end:]
    start=s.index('#define MM_MIXED_ENGINE_PATH');end=s.index('static unsigned char* mm_mixed_pixels;',start)
    s=s[:start]+'#include "mm_engine_identity.h"\n\n'+s[end:]
    p.write_text(s,encoding='utf-8')
    shutil.copy2(ROOT/'modernization/wrapper-probe/mm_engine_identity.h',ws/'src/mm_engine_identity.h')
