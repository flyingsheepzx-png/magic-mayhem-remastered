@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Battle-Sharpen-Light.ps1"
if errorlevel 1 pause
