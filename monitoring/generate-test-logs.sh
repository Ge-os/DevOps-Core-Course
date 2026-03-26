#!/bin/bash
# Lab 7 - Generate Test Logs
# This script generates various types of log entries for testing

echo "========================================="
echo "Generating Test Traffic for Lab 7"
echo "========================================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Generating successful requests to /..."
for i in {1..20}; do
    curl -s "$BASE_URL/" > /dev/null
    echo -n "."
done
echo " ✓ Done (20 requests)"

echo ""
echo "2. Generating health check requests..."
for i in {1..20}; do
    curl -s "$BASE_URL/health" > /dev/null
    echo -n "."
done
echo " ✓ Done (20 requests)"

echo ""
echo "3. Generating 404 errors..."
for i in {1..10}; do
    curl -s "$BASE_URL/nonexistent-endpoint" > /dev/null
    echo -n "."
done
echo " ✓ Done (10 requests)"

echo ""
echo "4. Generating requests with different user agents..."
user_agents=(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
    "curl/7.68.0"
    "PostmanRuntime/7.28.0"
    "Python-requests/2.26.0"
)

for ua in "${user_agents[@]}"; do
    curl -s -H "User-Agent: $ua" "$BASE_URL/" > /dev/null
    echo "  Request with UA: $ua"
done
echo " ✓ Done (4 requests)"

echo ""
echo "5. Rapid fire test (100 requests)..."
for i in {1..100}; do
    curl -s "$BASE_URL/" > /dev/null &
done
wait
echo " ✓ Done (100 concurrent requests)"

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Total requests generated: 174"
echo "- Successful (200): 144"
echo "- Not Found (404): 10"
echo "- Health checks: 20"
echo ""
echo "Check logs in:"
echo "1. Docker: docker logs devops-python-app"
echo "2. Grafana Explore: http://localhost:3000/explore"
echo "   Query: {app=\"devops-python\"}"
echo ""
echo "Wait 10-15 seconds for logs to be ingested by Loki"
echo "========================================="
