#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <vector>
#include <string>
#include <sstream>
#include <cstring>
using Loader=int(__fastcall*)(void*,void*,const char*);
using Free=void(__cdecl*)(void*);using Fail=void(__cdecl*)(int);using Balance=int(__cdecl*)();using Hash=void(__cdecl*)(const BYTE*,unsigned,char*);
static std::vector<BYTE> read(const std::wstring& path){FILE* f=nullptr;if(_wfopen_s(&f,path.c_str(),L"rb") || !f)return {};fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<BYTE>b(n);fread(b.data(),1,b.size(),f);fclose(f);return b;}
static std::string narrow(const std::wstring& text){int n=WideCharToMultiByte(CP_ACP,0,text.c_str(),-1,nullptr,0,nullptr,nullptr);std::vector<char> out(n);if(!n || !WideCharToMultiByte(CP_ACP,0,text.c_str(),-1,out.data(),n,nullptr,nullptr))return {};return out.data();}
int wmain(int argc,wchar_t** argv){
 if(argc!=4)return 2;HMODULE module=LoadLibraryW(argv[1]);if(!module)return 3;
 auto load=(Loader)GetProcAddress(module,"@mm_png_asset@12");auto release=(Free)GetProcAddress(module,"mm_png_test_free");auto fail=(Fail)GetProcAddress(module,"mm_png_test_fail");auto balance=(Balance)GetProcAddress(module,"mm_png_test_balance");auto hash=(Hash)GetProcAddress(module,"mm_png_test_sha");if(!load || !release || !fail || !balance || !hash)return 4;
 char hashed[65]{};hash((const BYTE*)"",0,hashed);if(strcmp(hashed,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 5;
 hash((const BYTE*)"abc",3,hashed);if(strcmp(hashed,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"))return 6;
 auto file=read(argv[2]);int n=MultiByteToWideChar(CP_UTF8,0,(const char*)file.data(),(int)file.size(),nullptr,0);std::wstring text(n,L'\0');MultiByteToWideChar(CP_UTF8,0,(const char*)file.data(),(int)file.size(),text.data(),n);std::wistringstream lines(text);std::wstring line;unsigned count=0;
 while(std::getline(lines,line)){
  if(line.empty())continue;size_t tab=line.find(L'\t'),next=line.find(L'\t',tab+1);if(tab==std::wstring::npos || next==std::wstring::npos)return 7;
  auto png=line.substr(0,tab),bmp=line.substr(tab+1,next-tab-1);auto original=read(bmp);if(original.size()<54)return 8;
  auto fh=(BITMAPFILEHEADER*)original.data();auto info=(BITMAPINFOHEADER*)(original.data()+14);int w=info->biWidth,h=info->biHeight;
  if(fh->bfType!=0x4d42 || info->biBitCount!=24 || info->biCompression!=BI_RGB || w<=0 || h<=0)return 9;
  void* object[2]{};std::wstring logical=png.substr(0,png.size()-4)+L".BMP";auto filename=narrow(logical);
  if(load(object,nullptr,filename.c_str())!=1 || !object[0] || !object[1] || balance()!=2)return 10;
  auto loaded=(BITMAPINFOHEADER*)object[0];int pitch=(w*3+3)&~3;
  if(loaded->biSize!=40 || loaded->biWidth!=w || loaded->biHeight!=h || loaded->biBitCount!=24 || loaded->biCompression!=BI_RGB || loaded->biSizeImage!=pitch*h)return 11;
  for(int y=0;y<h;y++)if(memcmp((BYTE*)object[1]+y*pitch,original.data()+fh->bfOffBits+y*pitch,w*3)){fwprintf(stderr,L"DIB mismatch %s\n",bmp.c_str());return 12;}
  // Exercise the same StretchDIBits origin/pitch/positive-height path as native.
  HDC dc=CreateCompatibleDC(nullptr);BITMAPINFO output{};output.bmiHeader.biSize=40;output.bmiHeader.biWidth=w;output.bmiHeader.biHeight=-h;output.bmiHeader.biPlanes=1;output.bmiHeader.biBitCount=32;void* pixels=nullptr;HBITMAP bitmap=CreateDIBSection(dc,&output,DIB_RGB_COLORS,&pixels,nullptr,0);if(!bitmap)return 13;auto prior=SelectObject(dc,bitmap);
  if(StretchDIBits(dc,0,0,w,h,0,0,w,h,object[1],(BITMAPINFO*)object[0],DIB_RGB_COLORS,SRCCOPY)!=h)return 14;GdiFlush();
  for(int y=0;y<h;y++)for(int x=0;x<w;x++)if(memcmp((BYTE*)pixels+(y*w+x)*4,original.data()+fh->bfOffBits+(h-1-y)*pitch+x*3,3))return 15;
  SelectObject(dc,prior);DeleteObject(bitmap);DeleteDC(dc);
  // Repeated load must replace and free both native-owned buffers.
  auto direct=narrow(png);if(load(object,nullptr,direct.c_str())!=1 || balance()!=2)return 16;
  if(count==0){
   void* a=object[0];void* b=object[1];fail(0);if(load(object,nullptr,filename.c_str())!=-7 || object[0]!=a || object[1]!=b || balance()!=2)return 17;
   fail(1);if(load(object,nullptr,filename.c_str())!=-7 || object[0]!=a || object[1]!=b || balance()!=2)return 18;fail(-1);
   if(load(nullptr,nullptr,filename.c_str())!=-7 || load(object,nullptr,nullptr)!=-7 || load(object,nullptr,"missing.BMP")!=-7 || load(object,nullptr,"untouched.JPG")!=-7)return 19;
   auto bad=narrow(argv[3]);if(load(object,nullptr,bad.c_str())!=-7 || balance()!=2)return 20;
  }
  release(object);if(balance()!=0)return 21;count++;
 }
 FreeLibrary(module);printf("{\"cases\":%u,\"DIB_RGB_exact\":true,\"GDI_RGB_exact\":true,\"allocation_replacement_and_failure\":\"passed\",\"fastcall_and_fallback\":\"passed\",\"SHA256_vectors\":\"passed\",\"game_launched\":false}\n",count);return count==770?0:22;
}
