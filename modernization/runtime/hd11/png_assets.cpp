// General native BMP image-object loader with lossless PNG storage.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wincodec.h>
#include <string>
#include <vector>
#include <cstring>
#include <cstdint>

static bool decode(const wchar_t* filename,std::vector<BYTE>& pixels,UINT& width,UINT& height,UINT& stride) {
    HRESULT initialized=CoInitializeEx(nullptr,COINIT_MULTITHREADED);
    if(FAILED(initialized) && initialized!=RPC_E_CHANGED_MODE)return false;
    IWICImagingFactory* factory=nullptr;IWICBitmapDecoder* decoder=nullptr;
    IWICBitmapFrameDecode* frame=nullptr;IWICFormatConverter* converter=nullptr;
    bool okay=false;GUID format{};UINT frames=0;
    HRESULT hr=CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory));
    if(FAILED(hr))goto done;
    hr=factory->CreateDecoderFromFilename(filename,nullptr,GENERIC_READ,WICDecodeMetadataCacheOnLoad,&decoder);
    if(FAILED(hr) || FAILED(decoder->GetContainerFormat(&format)) || !IsEqualGUID(format,GUID_ContainerFormatPng))goto done;
    if(FAILED(decoder->GetFrameCount(&frames)) || frames!=1 || FAILED(decoder->GetFrame(0,&frame)))goto done;
    if(FAILED(frame->GetSize(&width,&height)) || !width || !height || width>4096 || height>4096)goto done;
    if(FAILED(factory->CreateFormatConverter(&converter)))goto done;
    if(FAILED(converter->Initialize(frame,GUID_WICPixelFormat24bppBGR,WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom)))goto done;
    stride=(width*3+3)&~3u;
    pixels.assign(static_cast<size_t>(stride)*height,0);
    if(FAILED(converter->CopyPixels(nullptr,stride,static_cast<UINT>(pixels.size()),pixels.data())))goto done;
    okay=true;
done:
    if(converter)converter->Release();if(frame)frame->Release();if(decoder)decoder->Release();if(factory)factory->Release();
    if(SUCCEEDED(initialized))CoUninitialize();
    return okay;
}
#include <algorithm>
#ifdef MM_ASSET_TEST
static int allocations=0,frees=0,fail_after=-1;
static void* alloc_native(size_t size){if(fail_after==0)return nullptr;if(fail_after>0)fail_after--;void* p=HeapAlloc(GetProcessHeap(),0,size);if(p)allocations++;return p;}
static void free_native(void* p){if(p){HeapFree(GetProcessHeap(),0,p);frees++;}}
#else
static void* alloc_native(size_t size){using F=void*(__cdecl*)(size_t);return reinterpret_cast<F>(0x597880)(size);}
static void free_native(void* p){using F=void(__cdecl*)(void*);reinterpret_cast<F>(0x5979b0)(p);}
#endif
using NativeLoader=int(__thiscall*)(void*,const char*);
static NativeLoader original_loader=nullptr;
static int native_fallback(void* image,const char* filename){
#ifdef MM_ASSET_TEST
 (void)image;(void)filename;return -7;
#else
 return original_loader?original_loader(image,filename):0;
#endif
}
extern "C" __declspec(dllexport) void __cdecl mm_png_assets_anchor(){}
extern "C" __declspec(dllexport) int __fastcall mm_png_asset(void* object,void*,const char* filename){
 try {
  if(!object || !filename)return native_fallback(object,filename);
  std::string path(filename);auto dot=path.find_last_of('.');
  if(dot==std::string::npos || (_stricmp(path.c_str()+dot,".BMP") && _stricmp(path.c_str()+dot,".PNG")))return native_fallback(object,filename);
  path.replace(dot,std::string::npos,".PNG");
  int count=MultiByteToWideChar(CP_ACP,0,path.c_str(),-1,nullptr,0);
  if(count<=0 || count>32768)return native_fallback(object,filename);
  std::vector<wchar_t> wide(count);if(MultiByteToWideChar(CP_ACP,0,path.c_str(),-1,wide.data(),count)!=count)return native_fallback(object,filename);
  UINT w=0,h=0,stride=0;std::vector<BYTE> pixels;
  if(!decode(wide.data(),pixels,w,h,stride))return native_fallback(object,filename);
  void* header=alloc_native(0x428);if(!header)return native_fallback(object,filename);
  void* bits=alloc_native(pixels.size());if(!bits){free_native(header);return native_fallback(object,filename);}
  memset(header,0,0x428);auto info=static_cast<BITMAPINFOHEADER*>(header);
  info->biSize=40;info->biWidth=w;info->biHeight=h;info->biPlanes=1;info->biBitCount=24;info->biCompression=BI_RGB;info->biSizeImage=static_cast<DWORD>(pixels.size());
  // Preserve native positive-height bottom-up DIB layout and four-byte pitch.
  for(UINT y=0;y<h;y++)memcpy(static_cast<BYTE*>(bits)+static_cast<size_t>(h-1-y)*stride,pixels.data()+static_cast<size_t>(y)*stride,stride);
  auto fields=static_cast<void**>(object);free_native(fields[0]);free_native(fields[1]);fields[0]=header;fields[1]=bits;
  return 1;
 }catch(...){return native_fallback(object,filename);}
}
#ifdef MM_ASSET_TEST
extern "C" __declspec(dllexport) void __cdecl mm_png_test_free(void* object){auto f=(void**)object;free_native(f[0]);free_native(f[1]);f[0]=f[1]=nullptr;}
extern "C" __declspec(dllexport) void __cdecl mm_png_test_fail(int n){fail_after=n;}
extern "C" __declspec(dllexport) int __cdecl mm_png_test_balance(){return allocations-frees;}
#endif

// Self-contained SHA-256 avoids loading a crypto provider under the loader lock.
static uint32_t rotr(uint32_t n,unsigned b){return (n>>b)|(n<<(32-b));}
static std::string sha256(const std::vector<BYTE>& source){
 static const uint32_t k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
 uint32_t state[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
 std::vector<BYTE> data=source;uint64_t length=static_cast<uint64_t>(data.size())*8;data.push_back(0x80);while(data.size()%64!=56)data.push_back(0);
 for(int i=7;i>=0;i--)data.push_back(static_cast<BYTE>(length>>(8*i)));
 for(size_t start=0;start<data.size();start+=64){
  uint32_t w[64];for(int i=0;i<16;i++){size_t j=start+4*i;w[i]=(uint32_t(data[j])<<24)|(uint32_t(data[j+1])<<16)|(uint32_t(data[j+2])<<8)|data[j+3];}
  for(int i=16;i<64;i++){uint32_t s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3),s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10);w[i]=w[i-16]+s0+w[i-7]+s1;}
  uint32_t a=state[0],b=state[1],c=state[2],d=state[3],e=state[4],f=state[5],g=state[6],h=state[7];
  for(int i=0;i<64;i++){uint32_t s1=rotr(e,6)^rotr(e,11)^rotr(e,25),ch=(e&f)^((~e)&g),t1=h+s1+ch+k[i]+w[i],s0=rotr(a,2)^rotr(a,13)^rotr(a,22),maj=(a&b)^(a&c)^(b&c),t2=s0+maj;h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
  state[0]+=a;state[1]+=b;state[2]+=c;state[3]+=d;state[4]+=e;state[5]+=f;state[6]+=g;state[7]+=h;
 }
 std::string out;const char* digits="0123456789abcdef";for(uint32_t v:state)for(int shift=28;shift>=0;shift-=4)out+=digits[(v>>shift)&15];return out;
}
#ifdef MM_ASSET_TEST
extern "C" __declspec(dllexport) void __cdecl mm_png_test_sha(const BYTE* data,unsigned size,char* output){auto text=sha256(std::vector<BYTE>(data,data+size));memcpy(output,text.c_str(),65);}
#else
static bool known_engine(){
 wchar_t path[MAX_PATH];if(!GetModuleFileNameW(nullptr,path,MAX_PATH))return false;
 HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);if(file==INVALID_HANDLE_VALUE)return false;
 LARGE_INTEGER size{};bool valid=GetFileSizeEx(file,&size) && size.QuadPart>0 && size.QuadPart<8*1024*1024;
 std::vector<BYTE> data;DWORD count=0;if(valid){data.resize(static_cast<size_t>(size.QuadPart));valid=ReadFile(file,data.data(),static_cast<DWORD>(data.size()),&count,nullptr) && count==data.size();}CloseHandle(file);if(!valid)return false;
 auto h=sha256(data);
 return h=="b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291" || h=="be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7" || h=="43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d" || h=="3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d" || h=="42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da";
}
static bool install(){
 if(GetModuleHandleW(nullptr)!=(HMODULE)0x400000 || !known_engine())return false;
 BYTE* site=(BYTE*)0x486ae0;const BYTE expected[]={0x8b,0x44,0x24,0x04,0x83,0xec,0x38};if(memcmp(site,expected,7))return false;
 auto trampoline=(BYTE*)VirtualAlloc(nullptr,12,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);if(!trampoline)return false;
 memcpy(trampoline,expected,7);trampoline[7]=0xe9;*(int32_t*)(trampoline+8)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(site+7)-reinterpret_cast<uintptr_t>(trampoline+12));
 original_loader=(NativeLoader)trampoline;
 BYTE patch[7]={0xe9,0,0,0,0,0x90,0x90};*(int32_t*)(patch+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(&mm_png_asset)-reinterpret_cast<uintptr_t>(site+5));DWORD old=0;
 if(!VirtualProtect(site,7,PAGE_EXECUTE_READWRITE,&old)){original_loader=nullptr;VirtualFree(trampoline,0,MEM_RELEASE);return false;}
 memcpy(site,patch,7);FlushInstructionCache(GetCurrentProcess(),site,7);DWORD ignored;VirtualProtect(site,7,old,&ignored);return true;
}
#endif
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID){if(reason!=DLL_PROCESS_ATTACH)return TRUE;DisableThreadLibraryCalls(instance);
#ifdef MM_ASSET_TEST
 return TRUE;
#else
 try{return install()?TRUE:FALSE;}catch(...){return FALSE;}
#endif
}
