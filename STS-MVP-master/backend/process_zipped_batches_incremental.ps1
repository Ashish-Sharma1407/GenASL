param(
    [string]$DatasetRoot = "C:\Users\ashis\Downloads\DATASET",
    [string]$ProjectRoot = "C:\Users\ashis\Downloads\STS-MVP-master\STS-MVP-master",
    [switch]$KeepExtracted
)

$ErrorActionPreference = "Stop"

# Ensure recently installed tools (ffmpeg/ffprobe) are available in this session.
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

$backendDir = Join-Path $ProjectRoot "backend"
$rawDir = Join-Path $ProjectRoot "asllvd_raw"
$metaCsv = Join-Path $ProjectRoot "asllvd_metadata\asllvd_signs_2024_06_27.csv"
$py = Join-Path $backendDir ".venv\Scripts\python.exe"
$statusFile = Join-Path $ProjectRoot "pipeline_status.txt"

if (-not (Test-Path $DatasetRoot)) {
    throw "Dataset root not found: $DatasetRoot"
}

if (-not (Test-Path $py)) {
    throw "Backend Python venv missing: $py"
}

if (-not (Test-Path $metaCsv)) {
    throw "Metadata CSV missing: $metaCsv"
}

New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$zips = Get-ChildItem $DatasetRoot -File -Filter "batch_v3_*.zip" |
    Sort-Object {
        if ($_.BaseName -match "batch_v3_(\d+)") { [int]$matches[1] } else { 9999 }
    }

if (-not $zips) {
    throw "No batch_v3_*.zip files found in $DatasetRoot"
}

Write-Host "Found $($zips.Count) zip batches"
Set-Content -Path $statusFile -Value "STARTED $(Get-Date -Format s) total_batches=$($zips.Count)" -Encoding UTF8

$index = 0
foreach ($zip in $zips) {
    $index++
    Write-Host ""
    Write-Host "[$index/$($zips.Count)] Processing $($zip.Name)"
    Set-Content -Path $statusFile -Value "RUNNING $(Get-Date -Format s) batch=$index/$($zips.Count) file=$($zip.Name)" -Encoding UTF8

    $entries = tar -tf $zip.FullName
    if (-not $entries) {
        Write-Warning "Zip appears empty, skipping: $($zip.Name)"
        continue
    }

    tar -xf $zip.FullName -C $rawDir

    Push-Location $backendDir
    try {
        & $py asllvd_streaming_cutter.py
        & $py renaming_hash_clips.py
    }
    finally {
        Pop-Location
    }

    if (-not $KeepExtracted) {
        foreach ($entry in $entries) {
            if ([string]::IsNullOrWhiteSpace($entry)) { continue }
            $candidate = Join-Path $rawDir $entry
            if (Test-Path $candidate) {
                Remove-Item -Force $candidate
            }
        }
    }

    $clips = (Get-ChildItem (Join-Path $ProjectRoot "asl_videos\words") -File -Filter *.mp4 -ErrorAction SilentlyContinue).Count
    Write-Host "Current word clips: $clips"
    Set-Content -Path $statusFile -Value "RUNNING $(Get-Date -Format s) batch=$index/$($zips.Count) file=$($zip.Name) word_clips=$clips" -Encoding UTF8
}

Write-Host ""
Write-Host "Done."
Set-Content -Path $statusFile -Value "DONE $(Get-Date -Format s) total_batches=$($zips.Count)" -Encoding UTF8
