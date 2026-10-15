param([string]$Toolchain = 'D:/Tools/magic-mayhem-re/toolchain.json')
$ErrorActionPreference = 'Stop'
$config = Get-Content -LiteralPath $Toolchain -Raw | ConvertFrom-Json
$oldJava = $env:JAVA_HOME
$oldOverride = $env:JAVA_HOME_OVERRIDE
try {
    $env:JAVA_HOME = $config.java_home
    $env:JAVA_HOME_OVERRIDE = $config.java_home
    Push-Location -LiteralPath $config.ghidra_home
    try { & (Join-Path $config.ghidra_home 'ghidraRun.bat') }
    finally { Pop-Location }
} finally {
    $env:JAVA_HOME = $oldJava
    $env:JAVA_HOME_OVERRIDE = $oldOverride
}
