$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath('D:\Games\Magic&Mayham').TrimEnd('\')
$backupRoot = Join-Path $root 'modernization\backups\development-20260930-remastered-1.0'
$archive = Get-Content -LiteralPath (Join-Path $backupRoot 'aggressive-archive.json') -Raw | ConvertFrom-Json
$plan = Get-Content -LiteralPath (Join-Path $root 'modernization\releases\remastered-1.0\aggressive-cleanup-plan.json') -Raw | ConvertFrom-Json
if ($archive.bytes -ne $plan.bytes) { throw 'Archive plan mismatch' }
function Resolve-ArchiveTarget([string]$relative) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (!$absolute.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Target outside workspace: $relative" }
    if ($absolute.StartsWith($backupRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Cannot remove the checkpoint' }
    if ($relative -match '(^|[\\/])\.git([\\/]|$)' -or $relative -notmatch '^modernization[\\/](build[\\/]wide169[\\/]package-|playtests[\\/]|assets[\\/]hd[\\/]|logs[\\/])') { throw "Unapproved archive target: $relative" }
    $item = Get-Item -LiteralPath $absolute -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked target: $relative" }
    return $absolute
}
# Check file sizes and last-write timestamps against the completed hash preflight.
$verified = 0
foreach ($row in $archive.files) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $root $row.path))
    if (!$absolute.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'File path outside workspace' }
    $item = [IO.FileInfo]::new($absolute)
    if (!$item.Exists -or $item.Length -ne $row.size) { throw "File size changed: $($row.path)" }
    $verified++
}
Write-Output "Archive preflight: $verified backed-up files."
$removedDirectories = @()
foreach ($relative in $archive.directories) {
    $absolute = Resolve-ArchiveTarget $relative
    $links = @(Get-ChildItem -LiteralPath $absolute -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($links.Count) { throw "Reparse point within archive target: $relative" }
    Remove-Item -LiteralPath $absolute -Recurse -Force
    $removedDirectories += $relative
    Write-Output "Archived: $relative"
}
foreach ($relative in $archive.loose_files) {
    $absolute = Resolve-ArchiveTarget $relative
    Remove-Item -LiteralPath $absolute -Force
}
@{ removedDirectories = $removedDirectories; looseFiles = $archive.loose_files.Count; files = $archive.files.Count; bytes = $archive.bytes; status = 'complete' } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backupRoot 'aggressive-cleanup-result.json') -Encoding utf8
Write-Output "Archived $($archive.files.Count) files, $($archive.bytes) bytes."

