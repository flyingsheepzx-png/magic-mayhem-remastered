@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER "launcher-playtest.cpp" "D:\Games\Magic&Mayham\modernization\build\wide169.res" /Fo"launcher-playtest.obj" /link /SUBSYSTEM:WINDOWS /OUT:"game\Chaos-Mixed-UI-Preview.exe" bcrypt.lib user32.lib
set result=%errorlevel%
popd
exit /b %result%
