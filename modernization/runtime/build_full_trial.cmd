@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /W4 /DMM_COMBINED /DMM_ALL_IN_ONE "D:\Games\Magic&Mayham\modernization\runtime\repath_trial.cpp" "D:\Games\Magic&Mayham\modernization\runtime\render_replay_trial.cpp" "D:\Games\Magic&Mayham\modernization\runtime\clock_trial.cpp" "D:\Games\Magic&Mayham\modernization\runtime\logic_time_trial.cpp" "D:\Games\Magic&Mayham\modernization\runtime\game_time_trial.cpp" /Fo"D:\Games\Magic&Mayham\modernization\build\\" /link /OUT:"D:\Games\Magic&Mayham\modernization\build\full_trial.dll"
exit /b %errorlevel%
