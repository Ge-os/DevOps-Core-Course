# Lab 8 - Monitoring Stack Testing Script (PowerShell)
# This script tests observability components: Prometheus, Loki, Promtail, Grafana, and app metrics

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Lab 8 - Observability Stack Verification" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param(
        [string]$Url,
        [int]$ExpectedStatus,
        [string]$Name
    )
    
    Write-Host "Testing $Name... " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "✓ (HTTP $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ (HTTP $($response.StatusCode), expected $ExpectedStatus)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ (Failed to connect)" -ForegroundColor Red
        return $false
    }
}

Write-Host "1. Checking Docker Compose services..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
Push-Location $PSScriptRoot
docker compose ps --format table
Write-Host ""

Write-Host "2. Testing service endpoints..." -ForegroundColor Yellow
Write-Host "---------------------------------------"

# Test all endpoints
$endpoints = @(
    @{Url="http://localhost:3100/ready"; Status=200; Name="Loki /ready"}
    @{Url="http://localhost:3100/metrics"; Status=200; Name="Loki /metrics"}
    @{Url="http://localhost:9090/-/healthy"; Status=200; Name="Prometheus /-/healthy"}
    @{Url="http://localhost:9090/targets"; Status=200; Name="Prometheus /targets"}
    @{Url="http://localhost:9080/ready"; Status=200; Name="Promtail /ready"}
    @{Url="http://localhost:9080/targets"; Status=200; Name="Promtail /targets"}
    @{Url="http://localhost:3000/api/health"; Status=200; Name="Grafana /api/health"}
    @{Url="http://localhost:8000/"; Status=200; Name="Python App /"}
    @{Url="http://localhost:8000/health"; Status=200; Name="Python App /health"}
    @{Url="http://localhost:8000/metrics"; Status=200; Name="Python App /metrics"}
)

foreach ($endpoint in $endpoints) {
    Test-Endpoint -Url $endpoint.Url -ExpectedStatus $endpoint.Status -Name $endpoint.Name
}

Write-Host ""
Write-Host "3. Checking Promtail targets..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
try {
    $targetsResponse = Invoke-RestMethod -Uri "http://localhost:9080/targets" -UseBasicParsing
    $targetCount = $targetsResponse.activeTargets.Count
    Write-Host "Active targets: $targetCount"
    
    if ($targetCount -gt 0) {
        Write-Host "✓ Promtail is collecting logs from $targetCount targets" -ForegroundColor Green
        Write-Host ""
        Write-Host "Target details:"
        $targetsResponse.activeTargets | Select-Object -First 3 | ForEach-Object {
            Write-Host "  - Container: $($_.labels.container)" -ForegroundColor Cyan
            Write-Host "    App: $($_.labels.app)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✗ No active targets found" -ForegroundColor Red
        Write-Host "Check if containers have the 'logging=promtail' label"
    }
} catch {
    Write-Host "✗ Failed to query Promtail targets" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Checking Loki labels..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
try {
    $labelsResponse = Invoke-RestMethod -Uri "http://localhost:3100/loki/api/v1/labels" -UseBasicParsing
    if ($labelsResponse.data.Count -gt 0) {
        Write-Host "Available labels in Loki:"
        $labelsResponse.data | Select-Object -First 10 | ForEach-Object {
            Write-Host "  - $_" -ForegroundColor Cyan
        }
        Write-Host "✓ Loki has labels configured" -ForegroundColor Green
    } else {
        Write-Host "⚠ No labels found yet (logs may not have been ingested)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Failed to query Loki labels" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "5. Checking Docker container logs (JSON format)..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
$pythonAppLogs = docker logs devops-python-app --tail 3 2>&1
if ($pythonAppLogs) {
    Write-Host "Sample logs from Python app:"
    $pythonAppLogs | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    # Check if JSON
    try {
        $lastLog = docker logs devops-python-app --tail 1 2>&1 | Out-String
        $null = $lastLog | ConvertFrom-Json
        Write-Host "✓ Python app is logging in JSON format" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Python app logs may not be in JSON format" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Python app container not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "6. Testing Loki queries..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
try {
    $queryUrl = "http://localhost:3100/loki/api/v1/query?query={job=`"docker`"}&limit=5"
    $queryResponse = Invoke-RestMethod -Uri $queryUrl -UseBasicParsing
    $resultCount = $queryResponse.data.result.Count
    
    if ($resultCount -gt 0) {
        Write-Host "✓ Query returned $resultCount log streams" -ForegroundColor Green
    } else {
        Write-Host "⚠ No logs found (may need to generate some traffic first)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Failed to query Loki" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "7. Generating test traffic..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
Write-Host "Sending 20 requests to Python app..."

1..10 | ForEach-Object {
    $null = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -ErrorAction SilentlyContinue
    $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
}

Write-Host "✓ Generated 20 requests" -ForegroundColor Green
Write-Host "Waiting 10 seconds for logs to be ingested..."
Start-Sleep -Seconds 10

# Query again
try {
    $queryUrl = "http://localhost:3100/loki/api/v1/query?query={app=`"devops-python`"}&limit=5"
    $queryResponseAfter = Invoke-RestMethod -Uri $queryUrl -UseBasicParsing
    $resultCountAfter = $queryResponseAfter.data.result.Count
    
    if ($resultCountAfter -gt 0) {
        Write-Host "✓ Query returned $resultCountAfter log streams from Python app" -ForegroundColor Green
    } else {
        Write-Host "⚠ Still no logs from Python app" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Failed to query Loki after traffic generation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "8. Checking Prometheus targets..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
try {
    $upQuery = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/query?query=up" -UseBasicParsing
    $upCount = $upQuery.data.result.Count
    if ($upCount -gt 0) {
        Write-Host "✓ Prometheus up query returned $upCount target series" -ForegroundColor Green
    } else {
        Write-Host "✗ Prometheus up query returned no data" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Failed to query Prometheus" -ForegroundColor Red
}

Write-Host ""
Write-Host "9. Checking resource usage..." -ForegroundColor Yellow
Write-Host "---------------------------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "1. Access Grafana: http://localhost:3000"
Write-Host "   - Login: admin / (your password from .env)"
Write-Host "2. Access Prometheus: http://localhost:9090/targets"
Write-Host "3. In Grafana Explore run Loki query: {job=`"docker`"}"
Write-Host "4. In Grafana Explore run PromQL query: sum(rate(http_requests_total[5m]))"
Write-Host "5. Take screenshots for documentation"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  - View logs: docker compose logs -f [service]"
Write-Host "  - Restart:   docker compose restart [service]"
Write-Host "  - Stop all:  docker compose down"
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan

Pop-Location
