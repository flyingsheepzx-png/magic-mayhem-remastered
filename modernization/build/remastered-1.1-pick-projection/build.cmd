@echo off
call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 surface_registry_test.cpp /link /OUT:surface_registry_test.exe
if errorlevel 1 exit /b 1
surface_registry_test.exe
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 surface_lifecycle_native_test.cpp surface_lifecycle_test_hooks.cpp /link /BASE:0x10000000 /DYNAMICBASE:NO /OUT:surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
surface_lifecycle_native_test.exe
if errorlevel 1 exit /b 1
cl /nologo /LD /O2 /EHsc /std:c++17 /W4 qol_bindings.cpp mixed_ui_fonts.cpp campaign_ui.cpp port_drag.cpp confirm_dialog.cpp qwen_highlight.cpp window_close.cpp surface_lifecycle.cpp portrait_sprite_ready.cpp ai_budget.cpp ai_danger_refresh.cpp options_resolution.cpp options_window.cpp options_speed.cpp options_render.cpp /link /OUT:qol_bindings.dll /MAP:qol_bindings.map user32.lib
if errorlevel 1 exit /b 1
rc /nologo /focandidate.res candidate.rc
if errorlevel 1 exit /b 1
rc /nologo /forelease.res release.rc
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER launcher.cpp candidate.res /link /SUBSYSTEM:WINDOWS /OUT:candidate.exe bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DMM_ANIMATION_MOTION_LAUNCHER /DMM_LAYER_LAUNCHER /DMM_FULL_TRIAL_LAUNCHER /DMM_INSTALLED_LAUNCHER release_launcher.cpp release.res /link /SUBSYSTEM:WINDOWS /OUT:release.exe bcrypt.lib user32.lib
