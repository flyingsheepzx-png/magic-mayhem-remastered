@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /W4 /DMM_COMBINED "D:\Games\Magic&Mayham\modernization\runtime\repath_trial.cpp" "D:\Games\Magic&Mayham\modernization\runtime\render_replay_trial.cpp" /Fo"D:\Games\Magic&Mayham\modernization\build\\" /link /OUT:"D:\Games\Magic&Mayham\modernization\build\combined_trial.dll"
exit /b %errorlevel%
