$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$entry = Join-Path $root 'game\Chaos-Mixed-UI-Preview.exe'
$runtime = Join-Path $root 'game-wide169'
$manifest = Get-Content (Join-Path $root 'manifest.json') -Raw | ConvertFrom-Json
$files = @{
    'game/Chaos-Mixed-UI-Preview.exe' = $entry
    'game-wide169/Chaos-Wide169-engine.exe' = (Join-Path $runtime 'Chaos-Wide169-engine.exe')
    'game-wide169/ddraw.dll' = (Join-Path $runtime 'ddraw.dll')
}
foreach ($name in $files.Keys) {
    $actual = (Get-FileHash -LiteralPath $files[$name] -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $manifest.files.$name) { throw "Playtest package changed: $name" }
}
if ((Get-CimInstance Win32_Process | Where-Object { $_.Name -ieq 'Chaos-Wide169-engine.exe' }).Count -gt 0) {
    throw 'A game engine is already running; close it before starting this test.'
}
$previousRender = $env:MM_PROBE_MIXED_RENDER
$previousFonts = $env:MM_PROBE_MIXED_FONTS
$previousSharpen = $env:MM_PROBE_BATTLE_SHARPEN
try {
    $env:MM_PROBE_MIXED_RENDER = '1'
    $env:MM_PROBE_MIXED_FONTS = '1'
    $env:MM_PROBE_BATTLE_SHARPEN = '1'
    Start-Process -FilePath $entry -WorkingDirectory $runtime
} finally {
    $env:MM_PROBE_MIXED_RENDER = $previousRender
    $env:MM_PROBE_MIXED_FONTS = $previousFonts
    $env:MM_PROBE_BATTLE_SHARPEN = $previousSharpen
}
