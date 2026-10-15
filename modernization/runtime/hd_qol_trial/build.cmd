@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /LD /O2 /EHsc /std:c++17 /W4 "qol_bindings.cpp" /Fo"qol_bindings.obj" /link /OUT:"qol_bindings.dll" user32.lib
if errorlevel 1 (popd & exit /b 1)
rc /nologo /fo"hd_qol.res" "hd_qol.rc"
if errorlevel 1 (popd & exit /b 1)
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER "launcher.cpp" "hd_qol.res" /Fo"launcher.obj" /link /SUBSYSTEM:WINDOWS /OUT:"..\..\build\Chaos-HD60-QoL-Trial.exe" bcrypt.lib user32.lib
set result=%errorlevel%
popd
exit /b %result%
