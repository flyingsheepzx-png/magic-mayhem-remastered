@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist "obj" mkdir "obj"
cl /nologo /LD /O2 /EHsc /W4 /DMM_COMBINED /DMM_ALL_IN_ONE "repath_trial.cpp" "render_replay_trial.cpp" "clock_trial.cpp" "logic_time_trial.cpp" "game_time_trial.cpp" /Fo"obj\\" /link /OUT:"..\..\..\build\full60_rebuilt.dll"
set result=%errorlevel%
popd
exit /b %result%
