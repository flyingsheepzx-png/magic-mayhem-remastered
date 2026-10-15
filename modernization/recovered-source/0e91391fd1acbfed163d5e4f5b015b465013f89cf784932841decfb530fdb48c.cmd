@echo off
setlocal
set "MM_PROBE_MIXED_RENDER=1"
set "MM_PROBE_MIXED_FONTS=1"
if not exist "%~dp0game-wide169\modernization\logs" mkdir "%~dp0game-wide169\modernization\logs"
start "" "%~dp0game\Chaos-Mixed-UI-Preview.exe"
