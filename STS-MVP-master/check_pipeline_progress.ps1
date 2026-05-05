$proj = "C:\Users\ashis\Downloads\STS-MVP-master\STS-MVP-master"

$proc = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*process_zipped_batches_incremental.ps1*' }

$words = (Get-ChildItem "$proj\asl_videos\words" -Recurse -File -Filter *.mp4 -ErrorAction SilentlyContinue).Count
$raw = (Get-ChildItem "$proj\asllvd_raw" -Recurse -File -Include *.mov,*.mp4,*.avi -ErrorAction SilentlyContinue).Count
$poses = (Get-ChildItem "$proj\asl_videos\poses" -Recurse -File -Filter *.npy -ErrorAction SilentlyContinue).Count
$heads = (Get-ChildItem "$proj\asl_videos\heads" -Recurse -File -Filter *.npy -ErrorAction SilentlyContinue).Count

if ($proc) {
    Write-Host "STATUS: RUNNING"
    Write-Host "PROCESS_ID: $($proc.ProcessId -join ',')"
} else {
    Write-Host "STATUS: NOT RUNNING"
}

Write-Host "word_clips=$words"
Write-Host "raw_temp_files=$raw"
Write-Host "pose_files=$poses"
Write-Host "head_files=$heads"

$statusFile = Join-Path $proj "pipeline_status.txt"
if (Test-Path $statusFile) {
    Write-Host "status_file="
    Get-Content $statusFile
}
