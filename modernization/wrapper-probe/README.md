# Diagnostic cnc-ddraw build

This source patch counts wrapper surface uploads (`U`) and presentation attempts (`P`) separately. It is a measurement aid, not a gameplay patch or a 60 FPS implementation. It is used only by `modernization/tools/probe_session.py`, which backs up and restores the installed DLL and settings for each bounded test.

Pinned upstream: `https://github.com/FunkyFr3sh/cnc-ddraw.git`, commit `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.

Apply from the upstream checkout root:

```powershell
git apply 'D:\Games\Magic&Mayham\modernization\wrapper-probe\cnc-ddraw-probe.patch'
Copy-Item 'D:\Games\Magic&Mayham\modernization\wrapper-probe\mm_probe.h' .\inc\mm_probe.h
& 'C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe' .\cnc-ddraw.sln /p:Configuration=Release /p:Platform=Win32 /m
```

The MSBuild path is the one installed on the current test machine. `mm_probe.h` writes QPC tick timestamps into ignored `modernization/logs/wrapper-probe.csv` relative to the game's working directory. A present attempt can repeat the same game texture; the CSV is not a count of unique visual frames.
