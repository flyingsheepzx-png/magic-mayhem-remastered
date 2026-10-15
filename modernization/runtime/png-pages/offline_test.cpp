#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <vector>
#include <string>
#include <cstring>
struct FakeSurface {void** table;HDC dc;int fail_get=0,fail_release=0,gets=0,releases=0;};
static HRESULT WINAPI getdc(void* p,HDC* out){auto f=(FakeSurface*)p;f->gets++;if(f->fail_get)return E_FAIL;*out=f->dc;return S_OK;}
static HRESULT WINAPI releasedc(void* p,HDC dc){auto f=(FakeSurface*)p;f->releases++;return f->fail_release || dc!=f->dc?E_FAIL:S_OK;}
using Paint=int(__cdecl*)(void*,const wchar_t*);
using Page=int(__fastcall*)(void*,void*,const char*);
static std::vector<BYTE> bytes(const std::wstring& path){FILE* f=nullptr;if(_wfopen_s(&f,path.c_str(),L"rb") || !f)return {};fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<BYTE> b(n);fread(b.data(),1,b.size(),f);fclose(f);return b;}
int wmain(int argc,wchar_t** argv){
 if(argc!=4)return 2;
 HMODULE module=LoadLibraryW(argv[1]);if(!module)return 3;
 auto paint=(Paint)GetProcAddress(module,"mm_png_test_paint");auto page=(Page)GetProcAddress(module,"@mm_png_page@12");if(!paint || !page)return 4;
 std::wstring pngroot=argv[2],bmproot=argv[3];WIN32_FIND_DATAW entry{};HANDLE find=FindFirstFileW((pngroot+L"\\*.PNG").c_str(),&entry);if(find==INVALID_HANDLE_VALUE)return 5;
 unsigned count=0;void* table[27]{};table[17]=(void*)getdc;table[26]=(void*)releasedc;
 do {
  std::wstring file=entry.cFileName,png=pngroot+L"\\"+file,bmp=file.substr(0,file.size()-4)+L".BMP";
  auto data=bytes(bmproot+L"\\"+bmp);if(data.size()<54)return 6;
  auto header=(BITMAPFILEHEADER*)data.data();auto info=(BITMAPINFOHEADER*)(data.data()+14);int w=info->biWidth,h=info->biHeight;
  if(header->bfType!=0x4d42 || info->biBitCount!=24 || info->biCompression!=BI_RGB || w!=640 || h!=720)return 7;
  BITMAPINFO output{};output.bmiHeader.biSize=40;output.bmiHeader.biWidth=w;output.bmiHeader.biHeight=-h;output.bmiHeader.biPlanes=1;output.bmiHeader.biBitCount=32;void* pixels=nullptr;
  HDC dc=CreateCompatibleDC(nullptr);HBITMAP bitmap=CreateDIBSection(dc,&output,DIB_RGB_COLORS,&pixels,nullptr,0);if(!bitmap || !pixels)return 8;
  auto previous=SelectObject(dc,bitmap);FakeSurface surface{table,dc};BYTE image[28]{};*(void**)(image+8)=&surface;
  memset(pixels,0xcd,w*h*4);
  std::wstring simulated=pngroot+L"\\"+bmp;char filename[2048]{};
  if(!WideCharToMultiByte(CP_ACP,0,simulated.c_str(),-1,filename,sizeof(filename),nullptr,nullptr))return 9;
  if(page(image,nullptr,filename)!=1 || surface.gets!=1 || surface.releases!=1)return 10;
  GdiFlush();int stride=(w*3+3)&~3;
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){
   auto old=data.data()+header->bfOffBits+(h-1-y)*stride+x*3;auto now=(BYTE*)pixels+(y*w+x)*4;
   if(memcmp(old,now,3)){fwprintf(stderr,L"Pixel mismatch %s %d,%d\n",file.c_str(),x,y);return 11;}
  }
  if(count==0){
   if(paint(nullptr,png.c_str())!=0 || paint(image,L"missing.png")!=0)return 12;
   if(page(image,nullptr,"missing.BMP")!=-7 || page(image,nullptr,"missing.JPG")!=-7)return 13;
   surface.fail_get=1;if(paint(image,png.c_str())!=0)return 14;surface.fail_get=0;
   surface.fail_release=1;if(paint(image,png.c_str())!=0)return 15;surface.fail_release=0;
   auto invalid=pngroot+L"\\corrupt-test.tmp";if(paint(image,invalid.c_str())!=0)return 16;
  }
  SelectObject(dc,previous);DeleteObject(bitmap);DeleteDC(dc);count++;
 }while(FindNextFileW(find,&entry));FindClose(find);FreeLibrary(module);
 printf("{\"painted_pages\":%u,\"RGB_exact\":true,\"fastcall_stack\":\"passed\",\"failure_and_fallback_cases\":\"passed\",\"game_launched\":false}\n",count);
 return count==190?0:17;
}
