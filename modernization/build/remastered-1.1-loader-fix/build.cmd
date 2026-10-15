@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /MT /O2 /EHsc /std:c++17 /W4 png_assets.cpp /Fopng_assets.obj /link /OUT:png_assets.dll ole32.lib windowscodecs.lib
if errorlevel 1 exit /b 1
cl /nologo /LD /MT /O2 /EHsc /std:c++17 /W4 /DMM_ASSET_TEST png_assets.cpp /Fopng_assets_test.obj /link /OUT:png_assets_test.dll ole32.lib windowscodecs.lib
