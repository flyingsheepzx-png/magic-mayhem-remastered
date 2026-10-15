@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
rc /nologo /fo"..\..\..\build\full60_release.res" "full60_release.rc"
if errorlevel 1 (popd & exit /b 1)
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER "repath_debug_launcher.cpp" "..\..\..\build\full60_release.res" /Fo"..\..\..\build\full60_release_launcher.obj" /link /SUBSYSTEM:WINDOWS /OUT:"..\..\..\build\Chaos-Optimized-60.exe" bcrypt.lib user32.lib
set result=%errorlevel%
popd
exit /b %result%
