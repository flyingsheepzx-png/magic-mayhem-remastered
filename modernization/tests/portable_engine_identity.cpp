#include "mm_engine_identity.h"
#include <stdio.h>
int wmain(int argc,wchar_t** argv){
    if(argc!=3)return 2;
    BOOL allowed=mm_hd11_engine_file(argv[1]);
    int expected=argv[2][0]=='1';
    printf("engine identity allowed=%d expected=%d\n",allowed,expected);
    return !!allowed==expected?0:1;
}
