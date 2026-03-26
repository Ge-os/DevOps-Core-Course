# Lab 7 - Generate Test Logs (PowerShell)
# This script generates various types of log entries for testing

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Generating Test Traffic for Lab 7" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

Write-Host "1. Generating successful requests to /..." -ForegroundColor Yellow
1..20 | ForEach-Object {
    $null = Invoke-WebRequest -Uri "$baseUrl/" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "." -NoNewline
}
Write-Host " ✓ Done (20 requests)" -ForegroundColor Green

Write-Host ""
Write-Host "2. Generating health check requests..." -ForegroundColor Yellow
1..20 | ForEach-Object {
    $null = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "." -NoNewline
}
Write-Host " ✓ Done (20 requests)" -ForegroundColor Green

Write-Host ""
Write-Host "3. Generating 404 errors..." -ForegroundColor Yellow
1..10 | ForEach-Object {
    $null = Invoke-WebRequest -Uri "$baseUrl/nonexistent-endpoint" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "." -NoNewline
}
Write-Host " ✓ Done (10 requests)" -ForegroundColor Green

Write-Host ""
Write-Host "4. Generating requests with different user agents..." -ForegroundColor Yellow
$userAgents = @(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
    "curl/7.68.0",
    "PostmanRuntime/7.28.0",
    "Python-requests/2.26.0"
)

foreach ($ua in $userAgents) {
    $null = Invoke-WebRequest -Uri "$baseUrl/" -UserAgent $ua -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "  Request with UA: $ua"
}
Write-Host " ✓ Done (4 requests)" -ForegroundColor Green

Write-Host ""
Write-Host "5. Rapid fire test (100 requests)..." -ForegroundColor Yellow
$jobs = @()
1..100 | ForEach-Object {
    $jobs += Start-Job -ScriptBlock {
        param($url)
        $null = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction SilentlyContinue
    } -ArgumentList $baseUrl
}
$jobs | Wait-Job | Remove-Job
Write-Host " ✓ Done (100 concurrent requests)" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Total requests generated: 154"
Write-Host "- Successful (200): 124"
Write-Host "- Not Found (404): 10"
Write-Host "- Health checks: 20"
Write-Host ""
Write-Host "Check logs in:" -ForegroundColor Green
Write-Host "1. Docker: docker logs devops-python-app"
Write-Host "2. Grafana Explore: http://localhost:3000/explore"
Write-Host "   Query: {app=`"devops-python`"}"
Write-Host ""
Write-Host "Wait 10-15 seconds for logs to be ingested by Loki"
Write-Host "=========================================" -ForegroundColor Cyan
