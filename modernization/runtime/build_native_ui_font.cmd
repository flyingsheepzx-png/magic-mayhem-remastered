@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul
if errorlevel 1 exit /b 1
cl /nologo /c /O1 /GS- /Zl /Oi- /W4 /Fo"D:\Games\Magic&Mayham\modernization\build\native_ui_font.obj" "D:\Games\Magic&Mayham\modernization\runtime\native_ui_font_scale.c"
