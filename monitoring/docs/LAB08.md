# Lab 8: Metrics & Monitoring with Prometheus

**Student**: Selivanov George  
**Date**: March 19, 2026

## 1. Overview

This lab extends the existing observability stack from Lab 7 (Loki + Promtail + Grafana) with full metrics monitoring using Prometheus.

Implemented scope:
- Python app instrumentation with `prometheus_client`
- `/metrics` endpoint with RED metrics and app-specific metrics
- Prometheus 3.9 deployment and scrape configuration
- Grafana integration with Prometheus datasource
- Pre-provisioned dashboards (logs + metrics)
- Production hardening: health checks, resource limits, retention, persistence
- Ansible automation updated for full stack (bonus)

## 2. Architecture

### 2.1 Metrics Flow

```text
app-python (/metrics)
        |
        | scrape every 15s
        v
   Prometheus (TSDB, 15d/10GB retention)
        |
        | PromQL
        v
    Grafana dashboards
```

### 2.2 Full Observability Stack

```text
Docker containers -> Promtail -> Loki -> Grafana (logs)
app-python /metrics -> Prometheus -> Grafana (metrics)
```

## 3. Application Instrumentation

### 3.1 Dependency Added

File updated:
- `app_python/requirements.txt`

Added package:
- `prometheus-client==0.23.1`

### 3.2 Metrics Implemented

File updated:
- `app_python/app.py`

HTTP RED metrics:
- Counter: `http_requests_total{method,endpoint,status_code}`
- Histogram: `http_request_duration_seconds{method,endpoint}`
- Gauge: `http_requests_in_progress`

Application-specific metrics:
- Counter: `devops_info_endpoint_calls_total{endpoint}`
- Histogram: `devops_info_system_collection_seconds`

### 3.3 Endpoints

Implemented:
- `GET /metrics` returns Prometheus exposition format

Updated endpoint catalog (`GET /` response) to include `/metrics`.

### 3.4 Instrumentation Approach

- Middleware records:
  - request start time
  - in-progress gauge increment/decrement
  - response status code
  - histogram observation
  - counter increment with labels
- Endpoint labels are normalized using route path when available.

## 4. Prometheus Setup

### 4.1 Docker Compose Changes

File updated:
- `monitoring/docker-compose.yml`

Added service:
- `prometheus` with image `prom/prometheus:v3.9.0`
- Port mapping: `9090:9090`
- Config mount: `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
- Data volume: `prometheus-data:/prometheus`
- Retention flags:
  - `--storage.tsdb.retention.time=15d`
  - `--storage.tsdb.retention.size=10GB`

### 4.2 Prometheus Configuration

File created:
- `monitoring/prometheus/prometheus.yml`

Configured jobs:
- `prometheus` -> `localhost:9090`
- `app` -> `app-python:5000`, path `/metrics`
- `loki` -> `loki:3100`, path `/metrics`
- `grafana` -> `grafana:3000`, path `/metrics`

Global intervals:
- scrape interval: `15s`
- evaluation interval: `15s`

## 5. Grafana Dashboards

### 5.1 Datasource Provisioning

Files created:
- `monitoring/grafana/provisioning/datasources/prometheus.yml`
- `monitoring/grafana/provisioning/dashboards/dashboards.yml`

Grafana now auto-loads:
- Loki datasource
- Prometheus datasource
- Dashboards from `/var/lib/grafana/dashboards`

### 5.2 Dashboard Files

Files created:
- `monitoring/grafana/dashboards/grafana-app-dashboard.json`
- `monitoring/grafana/dashboards/grafana-logs-dashboard.json`

### 5.3 Metrics Dashboard Panels (7)

`grafana-app-dashboard.json` includes:
1. Request Rate by Endpoint
2. Error Rate (5xx)
3. Request Duration p95
4. Request Duration Heatmap
5. Active Requests
6. Status Code Distribution
7. App Uptime

Note: Label name is `status_code` (not `status`) because the implementation follows lab requirement labels: `method`, `endpoint`, `status_code`.

## 6. Production Configuration

### 6.1 Health Checks

Configured in compose for:
- Prometheus: `/-/healthy`
- Loki: `/ready`
- Promtail: `/ready`
- Grafana: `/api/health`
- App: `/health`

### 6.2 Resource Limits

Configured:
- Prometheus: `1G`, `1.0 CPU`
- Loki: `1G`, `1.0 CPU`
- Grafana: `512M`, `0.5 CPU`
- App: `256M`, `0.5 CPU`

### 6.3 Data Retention

Configured:
- Prometheus: `15d`, `10GB`
- Loki: existing retention from Lab 7 remains active (`168h`)

### 6.4 Persistence

Volumes:
- `prometheus-data`
- `loki-data`
- `grafana-data`
- `promtail-data`

## 7. PromQL Examples (RED + Ops)

1. Request rate by endpoint:
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

2. 5xx error rate:
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

3. p95 latency:
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

4. Current active requests:
```promql
http_requests_in_progress
```

5. Status code distribution:
```promql
sum by (status_code) (rate(http_requests_total[5m]))
```

6. Service uptime status:
```promql
up{job="app"}
```

7. Endpoint business usage:
```promql
sum(rate(devops_info_endpoint_calls_total[5m])) by (endpoint)
```

## 8. Testing Results

### 8.1 Automated Validation Performed

1. Python tests:
- Command: `python -m pytest -q`
- Result: **30 passed**

2. Lint:
- Command: `python -m ruff check .`
- Result: **All checks passed**

3. Docker Compose syntax:
- Command: `docker compose config` in `monitoring/`
- Result: **Valid**
- Note: compose warns `version` key is obsolete (non-blocking)

4. Ansible syntax check:
- Could not run because `ansible-playbook` is not installed in this environment.

## 9. Metrics vs Logs (Lab 7 Comparison)

Use **metrics** when you need:
- trends over time
- SLO/SLA tracking
- threshold alerting
- low-cost aggregation

Use **logs** when you need:
- request-level details
- stack traces and payload context
- forensic debugging
- exact event timelines

Best practice: use both together (implemented in this stack).

## 10. Challenges & Solutions

1. Missing test tooling in local Python runtime:
- Issue: `pytest` module missing
- Fix: configured venv and installed dependencies via `requirements.txt`

2. Label schema mismatch risk (`status` vs `status_code`):
- Issue: dashboards/examples often use `status`
- Fix: standardized to `status_code` across instrumentation and dashboard queries

3. Full stack automation gap in role:
- Issue: existing role provisioned only Loki datasource
- Fix: added Prometheus config templating, datasource provisioning, and dashboard provisioning

4. Local Ansible validation unavailable:
- Issue: `ansible-playbook` command not found
- Fix: provided manual verification algorithm below

## 11. Bonus — Ansible Automation Implemented

### 11.1 Role Enhancements

Updated role:
- `ansible/roles/monitoring/defaults/main.yml`
- `ansible/roles/monitoring/tasks/setup.yml`
- `ansible/roles/monitoring/tasks/deploy.yml`
- `ansible/roles/monitoring/templates/docker-compose.yml.j2`
- `ansible/roles/monitoring/templates/prometheus.yml.j2`
- `ansible/roles/monitoring/templates/grafana/datasources.yml.j2`
- `ansible/roles/monitoring/templates/grafana/dashboards.yml.j2`
- `ansible/roles/monitoring/files/grafana-app-dashboard.json`
- `ansible/roles/monitoring/files/grafana-logs-dashboard.json`

Capabilities added:
- Prometheus vars and templated scrape config
- Grafana auto-provisioning for Loki + Prometheus datasources
- Auto-provisioning of logs + metrics dashboards
- Readiness checks for Prometheus and datasource verification