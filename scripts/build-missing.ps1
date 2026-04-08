$ErrorActionPreference = "Stop"

Write-Host "Building Anomaly Detector..." -ForegroundColor Cyan
docker build -t anomaly-detector:latest anomaly-detector/

Write-Host "Building Decision Engine..." -ForegroundColor Cyan
docker build -t decision-engine:latest decision-engine/

Write-Host "Building Cyber Command Center UI..." -ForegroundColor Cyan
docker build -t cyber-command-center:latest ui/

Write-Host "All missing images built." -ForegroundColor Green
