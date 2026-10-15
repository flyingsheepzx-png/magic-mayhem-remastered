param(
    [Parameter(Mandatory)][string]$InputFile,
    [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$ProjectName,
    [string]$Toolchain = 'D:/Tools/magic-mayhem-re/toolchain.json',
    [string]$ProjectDirectory = 'D:/Tools/magic-mayhem-re/projects',
    [ValidateRange(1,3600)][int]$AnalysisTimeoutSeconds = 180,
    [ValidateRange(1,50000)][int]$MaxFunctions = 100
)
$ErrorActionPreference = 'Stop'
$config = Get-Content -LiteralPath $Toolchain -Raw | ConvertFrom-Json
$headless = Join-Path $config.ghidra_home 'support/analyzeHeadless.bat'
if (!(Test-Path -LiteralPath $headless)) { throw 'Missing Ghidra installation' }
if (!(Test-Path -LiteralPath (Join-Path $config.java_home 'bin/java.exe'))) { throw 'Missing JDK' }
$source = (Resolve-Path -LiteralPath $InputFile).Path
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $ExpectedSha256) {
    throw 'Input hash mismatch; no import performed'
}
$projectRoot = [IO.Path]::GetFullPath($ProjectDirectory)
if ($projectRoot -match '[&%!...^()]') { throw 'Use a project directory without cmd.exe metacharacters' }
$run = Join-Path $projectRoot ($ProjectName + '-export')
foreach ($path in @($run, (Join-Path $projectRoot ($ProjectName + '.gpr')), (Join-Path $projectRoot ($ProjectName + '.rep')))) {
    if (Test-Path -LiteralPath $path) { throw "Already exists; choose a new project name: $path" }
}
New-Item -ItemType Directory -Force -Path $projectRoot | Out-Null
New-Item -ItemType Directory -Path $run | Out-Null
$copy = Join-Path $run ([IO.Path]::GetFileName($source))
Copy-Item -LiteralPath $source -Destination $copy
$scriptDirectory = Join-Path $run 'scripts'
New-Item -ItemType Directory -Path $scriptDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ExportFunctions.java') -Destination $scriptDirectory
if ((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash -ne $ExpectedSha256 -or
    (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $ExpectedSha256) {
    throw 'Input changed during copy; abandon this import'
}
$oldJava = $env:JAVA_HOME
$oldOverride = $env:JAVA_HOME_OVERRIDE
try {
    $env:JAVA_HOME = $config.java_home
    $env:JAVA_HOME_OVERRIDE = $config.java_home
    $ghidraArgs = @($projectRoot, $ProjectName, '-import', $copy,
        '-analysisTimeoutPerFile', "$AnalysisTimeoutSeconds", '-max-cpu', '2',
        '-scriptPath', $scriptDirectory, '-postScript', 'ExportFunctions.java', $run, "$MaxFunctions",
        '-log', (Join-Path $run 'analysis.log'), '-scriptlog', (Join-Path $run 'scripts.log'))
    Push-Location -LiteralPath $config.ghidra_home
    try { & $headless @ghidraArgs } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "Ghidra exit code: $LASTEXITCODE" }
    if (!(Test-Path -LiteralPath (Join-Path $run 'export-complete.json'))) {
        throw 'Exporter did not complete; inspect analysis.log'
    }
    $unchanged = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -eq $ExpectedSha256
    [ordered]@{
        source = $source; sha256 = $ExpectedSha256.ToLowerInvariant(); source_unchanged = $unchanged
        toolchain = $config; project = $ProjectName; utc = [DateTime]::UtcNow.ToString('o')
        analysis_timeout_seconds = $AnalysisTimeoutSeconds; max_functions = $MaxFunctions
        baseline_promoted = $false; runtime_verified = $false
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'provenance.json') -Encoding utf8
    if (!$unchanged) { throw 'Source changed during analysis; exported copy is identified but source is no longer that version' }
    Write-Output "Static analysis export: $run"
} finally {
    $env:JAVA_HOME = $oldJava
    $env:JAVA_HOME_OVERRIDE = $oldOverride
}
