// PNG-first Grimoire page loader. Retains native BMP/JPEG fallback and exact RGB keys.
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
static bool paint(void* image,const wchar_t* filename) {
    if(!image)return false;
    auto surface=*reinterpret_cast<void**>(static_cast<BYTE*>(image)+8);
    if(!surface)return false;
    std::vector<BYTE> pixels;UINT w=0,h=0,stride=0;
    if(!decode(filename,pixels,w,h,stride))return false;
    auto table=*reinterpret_cast<void***>(surface);
    using GetDC=HRESULT (WINAPI*)(void*,HDC*);using ReleaseDC=HRESULT (WINAPI*)(void*,HDC);
    HDC dc=nullptr;
    if(FAILED(reinterpret_cast<GetDC>(table[17])(surface,&dc)) || !dc)return false;
    BITMAPINFO info{};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth=static_cast<LONG>(w);info.bmiHeader.biHeight=-static_cast<LONG>(h);
    info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=24;info.bmiHeader.biCompression=BI_RGB;
    // Same 1:1 SRCCOPY GDI path as native BMP loader; no scaling, profiles or alpha.
    int copied=StretchDIBits(dc,0,0,w,h,0,0,w,h,pixels.data(),&info,DIB_RGB_COLORS,SRCCOPY);
    HRESULT released=reinterpret_cast<ReleaseDC>(table[26])(surface,dc);
    return copied==static_cast<int>(h) && SUCCEEDED(released);
}
#ifdef MM_PNG_TEST
extern "C" __declspec(dllexport) int __cdecl mm_png_test_paint(void* image,const wchar_t* filename) {
    try{return paint(image,filename)?1:0;}catch(...){return 0;}
}
#endif
static int native_bmp(void* image,const char* filename) {
#ifdef MM_PNG_TEST
    (void)image;(void)filename;return -7;
#else
    using Native=int (__thiscall*)(void*,const char*);
    return reinterpret_cast<Native>(0x58d1a0)(image,filename);
#endif
}
extern "C" __declspec(dllexport) int __fastcall mm_png_page(void* image,void*,const char* filename) {
    try {
        if(filename){
            std::string path(filename);auto dot=path.find_last_of('.');
            if(dot!=std::string::npos && (!_stricmp(path.c_str()+dot,".BMP") || !_stricmp(path.c_str()+dot,".PNG") || !_stricmp(path.c_str()+dot,".JPG"))){
                path.replace(dot,std::string::npos,".PNG");
                int count=MultiByteToWideChar(CP_ACP,0,path.c_str(),-1,nullptr,0);
                if(count>0 && count<=32768){
                    std::vector<wchar_t> wide(count);
                    if(MultiByteToWideChar(CP_ACP,0,path.c_str(),-1,wide.data(),count)==count && paint(image,wide.data()))return 1;
                }
            }
        }
    }catch(...){ }
    return native_bmp(image,filename);
}
#ifndef MM_PNG_TEST
static int __fastcall png_or_jpeg(void* image,void*,const char* filename){
    int result=mm_png_page(image,nullptr,filename);
    if(result)return result;
    using Native=int(__thiscall*)(void*,const char*);
    return reinterpret_cast<Native>(0x58d320)(image,filename);
}
static bool install(){
    if(GetModuleHandleW(nullptr)!=reinterpret_cast<HMODULE>(0x400000))return false;
    struct Call{unsigned site,target;void* hook;};
    Call calls[]={{0x4c532f,0x58d1a0,(void*)mm_png_page},
        {0x4c5380,0x58d320,(void*)png_or_jpeg},
        {0x4c574c,0x58d320,(void*)png_or_jpeg},
        {0x4c575c,0x58d1a0,(void*)mm_png_page},
        {0x4c3d7e,0x58d320,(void*)png_or_jpeg},
        {0x4c3dcc,0x58d1a0,(void*)mm_png_page}};
    for(auto c:calls){auto* site=(BYTE*)c.site;
        if(site[0]!=0xe8 || c.site+5+*(int32_t*)(site+1)!=c.target)return false;}
    for(auto c:calls){auto* site=(BYTE*)c.site;BYTE replacement[5]={0xe8};
        *(int32_t*)(replacement+1)=static_cast<int32_t>((uintptr_t)c.hook-(c.site+5));
        DWORD old=0,ignored=0;if(!VirtualProtect(site,5,PAGE_EXECUTE_READWRITE,&old))return false;
        memcpy(site,replacement,5);FlushInstructionCache(GetCurrentProcess(),site,5);
        VirtualProtect(site,5,old,&ignored);}
    return true;
}
#endif
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID){
    if(reason!=DLL_PROCESS_ATTACH)return TRUE;DisableThreadLibraryCalls(instance);
#ifdef MM_PNG_TEST
    return TRUE;
#else
    return install()?TRUE:FALSE;
#endif
}
