@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
rc /nologo /focandidate.res candidate.rc
if errorlevel 1 exit /b 1
rc /nologo /forelease.res release.rc
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:candidate.exe bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER release_launcher.cpp release.res /link /SUBSYSTEM:WINDOWS /OUT:release.exe bcrypt.lib user32.lib
