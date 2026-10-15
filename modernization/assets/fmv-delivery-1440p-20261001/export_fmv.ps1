$ErrorActionPreference='Stop'
$taskOut='D:/Games/Magic&Mayham/modernization/assets/fmv-delivery-1440p-20261001'
$staged='D:/Tools/magic-mayhem-re/projects/fmv-h264-11-20261001-export/scripts'
Copy-Item -LiteralPath "$taskOut/FMVExport.java" -Destination $staged
$env:JAVA_HOME='D:/Tools/magic-mayhem-re/jdk-21.0.12.1+1'
$env:JAVA_HOME_OVERRIDE=$env:JAVA_HOME
Push-Location 'D:/Tools/magic-mayhem-re'
try {
 & 'D:/Tools/magic-mayhem-re/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat' 'D:/Tools/magic-mayhem-re/projects' 'fmv-h264-11-20261001' -process 'Chaos-Wide169-engine.exe' -noanalysis -scriptPath $staged -postScript FMVExport.java 'D:/Tools/magic-mayhem-re/projects/fmv-h264-11-20261001-export'
 if($LASTEXITCODE -ne 0){throw "Ghidra failed: $LASTEXITCODE"}
 foreach($name in @('4696e0.c','469830.c','469a00.c')){Copy-Item -LiteralPath "D:/Tools/magic-mayhem-re/projects/fmv-h264-11-20261001-export/$name" -Destination $taskOut}
} finally {Pop-Location}
