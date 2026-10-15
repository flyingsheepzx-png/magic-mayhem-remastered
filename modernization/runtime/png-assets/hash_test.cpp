#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <vector>
#include <cstring>
using Hash=void(__cdecl*)(const BYTE*,unsigned,char*);
int wmain(int argc,wchar_t** argv){
 if(argc<5 || (argc-3)%2)return 2;
 // Production module must refuse the test host rather than patching unknown code.
 HMODULE denied=LoadLibraryW(argv[2]);if(denied){FreeLibrary(denied);return 3;}
 HMODULE test=LoadLibraryW(argv[1]);if(!test)return 4;auto hash=(Hash)GetProcAddress(test,"mm_png_test_sha");if(!hash)return 5;
 unsigned checks=0;
 for(int i=3;i<argc;i+=2){FILE* f=nullptr;if(_wfopen_s(&f,argv[i],L"rb") || !f)return 6;fseek(f,0,SEEK_END);long size=ftell(f);rewind(f);std::vector<BYTE> bytes(size);fread(bytes.data(),1,bytes.size(),f);fclose(f);char got[65]{};hash(bytes.data(),(unsigned)bytes.size(),got);char expected[65]{};WideCharToMultiByte(CP_ACP,0,argv[i+1],-1,expected,65,nullptr,nullptr);if(strcmp(got,expected))return 7;checks++;}
 FreeLibrary(test);printf("{\"engine_SHA256_checks\":%u,\"unknown_engine_refused\":true}\n",checks);return 0;
}
