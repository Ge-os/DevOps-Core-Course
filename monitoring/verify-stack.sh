#!/bin/bash
# Lab 7 - Monitoring Stack Testing Script
# This script tests all components of the Loki monitoring stack

set -e  # Exit on error

echo "========================================="
echo "Lab 7 - Loki Stack Verification"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected=$2
    local name=$3
    
    echo -n "Testing $name... "
    response=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $response, expected $expected)"
        return 1
    fi
}

echo "1. Checking Docker Compose services..."
echo "---------------------------------------"
cd "$(dirname "$0")"

if docker compose ps --format json > /dev/null 2>&1; then
    services=$(docker compose ps --format json | jq -r '.[].Service' 2>/dev/null || docker compose ps --services)
    echo "Services detected: $services"
    
    # Check each service status
    docker compose ps --format table
    echo ""
else
    echo -e "${RED}✗${NC} Docker Compose not running or not in correct directory"
    echo "Please run this script from the monitoring directory"
    exit 1
fi

echo ""
echo "2. Testing service endpoints..."
echo "---------------------------------------"

# Test Loki
test_endpoint "http://localhost:3100/ready" "200" "Loki /ready"
test_endpoint "http://localhost:3100/metrics" "200" "Loki /metrics"

# Test Promtail
test_endpoint "http://localhost:9080/ready" "200" "Promtail /ready"
test_endpoint "http://localhost:9080/targets" "200" "Promtail /targets"

# Test Grafana
test_endpoint "http://localhost:3000/api/health" "200" "Grafana /api/health"

# Test Python App
test_endpoint "http://localhost:8000/" "200" "Python App /"
test_endpoint "http://localhost:8000/health" "200" "Python App /health"

echo ""
echo "3. Checking Promtail targets..."
echo "---------------------------------------"
targets=$(curl -s http://localhost:9080/targets 2>/dev/null | jq '.activeTargets | length' 2>/dev/null || echo "0")
echo "Active targets: $targets"

if [ "$targets" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Promtail is collecting logs from $targets targets"
    echo ""
    echo "Target details:"
    curl -s http://localhost:9080/targets | jq '.activeTargets[] | {labels: .labels, discoveredLabels: .discoveredLabels}' | head -30
else
    echo -e "${RED}✗${NC} No active targets found"
    echo "Check if containers have the 'logging=promtail' label"
fi

echo ""
echo "4. Checking Loki labels..."
echo "---------------------------------------"
labels=$(curl -s http://localhost:3100/loki/api/v1/labels 2>/dev/null | jq -r '.data[]' 2>/dev/null || echo "")
if [ -n "$labels" ]; then
    echo "Available labels in Loki:"
    echo "$labels" | head -20
    echo -e "${GREEN}✓${NC} Loki has labels configured"
else
    echo -e "${YELLOW}⚠${NC} No labels found yet (logs may not have been ingested)"
fi

echo ""
echo "5. Checking Docker container logs (JSON format)..."
echo "---------------------------------------"
if docker ps --format "{{.Names}}" | grep -q "devops-python-app"; then
    echo "Sample log from Python app:"
    docker logs devops-python-app 2>&1 | tail -3
    
    # Check if logs are JSON
    if docker logs devops-python-app 2>&1 | tail -1 | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Python app is logging in JSON format"
    else
        echo -e "${YELLOW}⚠${NC} Python app logs may not be in JSON format"
    fi
else
    echo -e "${YELLOW}⚠${NC} Python app container not found"
fi

echo ""
echo "6. Testing Loki queries..."
echo "---------------------------------------"

# Query all logs from docker job
echo "Query: {job=\"docker\"}"
query_result=$(curl -s -G "http://localhost:3100/loki/api/v1/query" \
    --data-urlencode 'query={job="docker"}' \
    --data-urlencode 'limit=5' 2>/dev/null | jq '.data.result | length' 2>/dev/null || echo "0")

if [ "$query_result" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Query returned $query_result log streams"
else
    echo -e "${YELLOW}⚠${NC} No logs found (may need to generate some traffic first)"
fi

echo ""
echo "7. Generating test traffic..."
echo "---------------------------------------"
echo "Sending 20 requests to Python app..."

for i in {1..10}; do
    curl -s http://localhost:8000/ > /dev/null 2>&1
    curl -s http://localhost:8000/health > /dev/null 2>&1
done

echo -e "${GREEN}✓${NC} Generated 20 requests"
echo "Wait 10 seconds for logs to be ingested..."
sleep 10

# Query again after generating traffic
echo ""
echo "Query after generating traffic: {app=\"devops-python\"}"
query_result_after=$(curl -s -G "http://localhost:3100/loki/api/v1/query" \
    --data-urlencode 'query={app="devops-python"}' \
    --data-urlencode 'limit=5' 2>/dev/null | jq '.data.result | length' 2>/dev/null || echo "0")

if [ "$query_result_after" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Query returned $query_result_after log streams from Python app"
else
    echo -e "${YELLOW}⚠${NC} Still no logs from Python app"
fi

echo ""
echo "8. Checking resource usage..."
echo "---------------------------------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep -E "loki|promtail|grafana|devops-python"

echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Access Grafana: http://localhost:3000"
echo "   - Login: admin / (your password from .env)"
echo "2. Go to Explore and run queries:"
echo "   - {job=\"docker\"}"
echo "   - {app=\"devops-python\"} | json"
echo "3. Create dashboard with panels (see LAB07.md section 4.2)"
echo "4. Take screenshots for documentation"
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose logs -f [service]"
echo "  - Restart:   docker compose restart [service]"
echo "  - Stop all:  docker compose down"
echo ""
echo "========================================="
