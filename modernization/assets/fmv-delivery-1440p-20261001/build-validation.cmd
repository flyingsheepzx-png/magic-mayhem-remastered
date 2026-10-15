@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /MT /O2 /EHsc /std:c++17 fmv_h264_validation.cpp /link /OUT:fmv_h264_validation.dll mfplay.lib mfplat.lib mfuuid.lib ole32.lib bcrypt.lib user32.lib gdi32.lib
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /EHsc /std:c++17 playback_host.cpp /link /OUT:playback_host.exe user32.lib
