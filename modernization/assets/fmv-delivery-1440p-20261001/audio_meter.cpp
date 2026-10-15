#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmdeviceapi.h>
#include <audiopolicy.h>
#include <endpointvolume.h>
#include <cstdio>
#include <cstdlib>
#pragma comment(lib,"ole32.lib")
int main(int argc,char** argv){
 if(argc!=2)return 2;DWORD wanted=strtoul(argv[1],nullptr,10);CoInitializeEx(nullptr,COINIT_MULTITHREADED);
 IMMDeviceEnumerator* enumerator=nullptr;HRESULT hr=CoCreateInstance(__uuidof(MMDeviceEnumerator),nullptr,CLSCTX_ALL,IID_PPV_ARGS(&enumerator));if(FAILED(hr))return 3;
 float maximum=0;int found=0;bool muted=false;
 for(int tick=0;tick<40;tick++){
  IMMDeviceCollection* devices=nullptr;if(SUCCEEDED(enumerator->EnumAudioEndpoints(eRender,DEVICE_STATE_ACTIVE,&devices))){UINT count;devices->GetCount(&count);
   for(UINT i=0;i<count;i++){IMMDevice* device=nullptr;IAudioSessionManager2* manager=nullptr;IAudioSessionEnumerator* sessions=nullptr;
    if(SUCCEEDED(devices->Item(i,&device))&&SUCCEEDED(device->Activate(__uuidof(IAudioSessionManager2),CLSCTX_ALL,nullptr,(void**)&manager))&&SUCCEEDED(manager->GetSessionEnumerator(&sessions))){int n;sessions->GetCount(&n);
     for(int j=0;j<n;j++){IAudioSessionControl* control=nullptr;IAudioSessionControl2* info=nullptr;IAudioMeterInformation* meter=nullptr;ISimpleAudioVolume* volume=nullptr;
      if(SUCCEEDED(sessions->GetSession(j,&control))&&SUCCEEDED(control->QueryInterface(IID_PPV_ARGS(&info)))){DWORD pid=0;info->GetProcessId(&pid);if(pid==wanted){found++;if(SUCCEEDED(control->QueryInterface(IID_PPV_ARGS(&meter)))){float value=0;meter->GetPeakValue(&value);if(value>maximum)maximum=value;}if(SUCCEEDED(control->QueryInterface(IID_PPV_ARGS(&volume)))){BOOL m=FALSE;volume->GetMute(&m);muted=muted||m;}}}
      if(volume)volume->Release();if(meter)meter->Release();if(info)info->Release();if(control)control->Release();
     }
    }if(sessions)sessions->Release();if(manager)manager->Release();if(device)device->Release();
   }devices->Release();
  }Sleep(200);
 }
 enumerator->Release();CoUninitialize();printf("{\"pid\":%lu,\"audio_session_samples\":%d,\"peak\":%.8f,\"muted\":%s}\n",wanted,found,maximum,muted?"true":"false");return found&&maximum>0.0001&&!muted?0:1;
}
