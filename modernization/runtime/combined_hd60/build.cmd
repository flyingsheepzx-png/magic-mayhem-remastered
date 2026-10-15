@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist "obj" mkdir "obj"
cl /nologo /LD /O2 /EHsc /W4 /DMM_COMBINED /DMM_ALL_IN_ONE "repath_trial.cpp" "render_replay_trial.cpp" "clock_trial.cpp" "logic_time_trial.cpp" "game_time_trial.cpp" /Fo"obj\\" /link /OUT:"combined_hd60.dll"
if errorlevel 1 (popd & exit /b 1)
rc /nologo /fo"..\..\build\combined_hd60.res" "combined.rc"
if errorlevel 1 (popd & exit /b 1)
cl /nologo /O2 /EHsc /std:c++17 /W4 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER "launcher.cpp" "..\..\build\combined_hd60.res" /Fo"obj\combined_launcher.obj" /link /SUBSYSTEM:WINDOWS /OUT:"..\..\build\Chaos-HD60-Trial.exe" bcrypt.lib user32.lib
set result=%errorlevel%
popd
exit /b %result%
