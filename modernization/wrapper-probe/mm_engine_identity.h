#ifndef MM_ENGINE_IDENTITY_H
#define MM_ENGINE_IDENTITY_H
#include <windows.h>
#include <bcrypt.h>
#include <string.h>
#pragma comment(lib,"bcrypt.lib")
/* Portable release identity; no directory name authorizes engine addresses. */
static BOOL mm_hd11_engine_file(const wchar_t* path)
{
    static const unsigned char expected[32]={
        0x42,0xf2,0xaa,0xc7,0xee,0x8f,0x61,0xc0,0x00,0xf8,0x5b,0x92,0xee,0x6d,0x6a,0xfa,
        0x42,0xf2,0xdc,0xfc,0xdd,0x95,0x18,0x8d,0x55,0xf0,0x41,0xba,0xc8,0xa5,0x17,0xda};
    HANDLE file=INVALID_HANDLE_VALUE;BCRYPT_ALG_HANDLE algorithm=NULL;
    BCRYPT_HASH_HANDLE hash=NULL;unsigned char buffer[65536],digest[32];
    DWORD got=0;BOOL ok=FALSE,read_ok;
    file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE)goto finish;
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,NULL,0)<0)goto finish;
    if(BCryptCreateHash(algorithm,&hash,NULL,0,NULL,0,0)<0)goto finish;
    for(;;){
        read_ok=ReadFile(file,buffer,sizeof(buffer),&got,NULL);
        if(!read_ok)goto finish;if(!got)break;
        if(BCryptHashData(hash,buffer,got,0)<0)goto finish;
    }
    if(BCryptFinishHash(hash,digest,sizeof(digest),0)<0)goto finish;
    ok=memcmp(digest,expected,sizeof(digest))==0;
finish:
    if(hash)BCryptDestroyHash(hash);
    if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);
    if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);
    return ok;
}
static BOOL mm_hd11_current_engine(void)
{
    wchar_t path[32768];DWORD size=GetModuleFileNameW(NULL,path,32768);
    return size && size<32768 && mm_hd11_engine_file(path);
}
#endif
