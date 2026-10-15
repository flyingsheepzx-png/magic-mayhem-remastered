@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /W4 "D:\Games\Magic&Mayham\modernization\runtime\render_replay_trial.cpp" /Fo"D:\Games\Magic&Mayham\modernization\build\render_replay_trial.obj" /link /OUT:"D:\Games\Magic&Mayham\modernization\build\render_replay_trial.dll"
exit /b %errorlevel%
