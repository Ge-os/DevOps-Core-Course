# Lab 7: Observability & Logging with Loki Stack

**Student**: Selivanov George  
**Date**: March 12, 2026

## 1. Overview

This lab implements a complete centralized logging solution using the Grafana Loki stack. The setup includes Loki 3.0 for log aggregation with TSDB storage, Promtail 3.0 for log collection from Docker containers, and Grafana 11.3.1 for visualization and dashboards.

### 1.1 Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **Loki** | 3.0.0 | Log aggregation and storage with TSDB |
| **Promtail** | 3.0.0 | Log collector for Docker containers |
| **Grafana** | 11.3.1 | Visualization and dashboards |
| **Python App** | 1.0.0 | DevOps Info Service with JSON logging |

### 1.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Logging Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐        ┌────────────────┐              │
│  │  Python App    │        │  Other Apps    │              │
│  │  (JSON Logs)   │        │  (JSON Logs)   │              │
│  └────────┬───────┘        └────────┬───────┘              │
│           │                         │                        │
│           └─────────┬───────────────┘                        │
│                     │                                         │
│                     ↓  Docker logs via                       │
│              ┌──────────────┐  /var/lib/docker/containers   │
│              │   Promtail   │                                │
│              │ (Collector)  │  ← Docker Socket (discovery)  │
│              └──────┬───────┘                                │
│                     │ HTTP Push                              │
│                     ↓                                         │
│              ┌──────────────┐                                │
│              │     Loki      │                                │
│              │  (Storage)   │  ← TSDB + 7-day retention     │
│              └──────┬───────┘                                │
│                     │ LogQL Queries                          │
│                     ↓                                         │
│              ┌──────────────┐                                │
│              │   Grafana    │                                │
│              │ (Dashboards) │  ← Web UI (localhost:3000)    │
│              └──────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow**:
1. Applications write logs to stdout (JSON format)
2. Docker captures logs in `/var/lib/docker/containers`
3. Promtail discovers containers via Docker socket
4. Promtail reads logs and pushes to Loki
5. Loki stores logs with TSDB indexing
6. Grafana queries logs via LogQL
7. Users visualize logs in dashboards

### 1.3 Why Loki Over Elasticsearch?

**Key Differences**:

| Feature | Loki | Elasticsearch |
|---------|------|---------------|
| **Indexing Strategy** | Only metadata (labels) | Full-text indexing |
| **Storage Cost** | Very low (5-10x cheaper) | High |
| **Query Performance** | Fast for label-based queries | Fast for full-text search |
| **Resource Usage** | Low (100-500 MB RAM) | High (2-8 GB RAM minimum) |
| **Complexity** | Simple deployment | Complex cluster management |
| **Best For** | Container logs, metrics | Complex search, analytics |

**Why Loki for This Lab**:
- **Lightweight**: Perfect for development and small-scale deployments
- **Label-Based**: Container metadata (app name, environment) as labels
- **Cost-Effective**: Minimal storage and resource requirements
- **Native Grafana**: Seamless integration with Grafana ecosystem
- **Container-First**: Designed specifically for cloud-native logs

---

## 2. Task 1 — Deploy Loki Stack (4 pts)

### 2.1 Understanding Log Labels

**Labels in Loki** are key-value pairs attached to log streams:
- Used for indexing and querying
- Should be low-cardinality (few unique values)
- Examples: `app`, `environment`, `container`, `job`

**Good Labels**:
```
{app="devops-python", environment="dev", level="ERROR"}
```

**Bad Labels** (high cardinality):
```
{request_id="uuid-123456", user_id="user-789", timestamp="2026-03-12..."}
```

**Why It Matters**:
- Too many label combinations = poor performance
- Labels create separate log streams
- Store high-cardinality data in log lines, not labels

### 2.2 Promtail Container Discovery

**Docker Service Discovery** (`docker_sd_configs`):
- Connects to Docker socket: `/var/run/docker.sock`
- Automatically discovers running containers
- Filters containers by label: `logging=promtail`
- Extracts metadata: container name, ID, labels, image

**Relabeling Process**:
1. `__meta_docker_container_name` -> `container` label
2. `__meta_docker_container_label_app` -> `app` label
3. Remove leading `/` from container names with regex
4. Add static labels like `job="docker"`

**Security Consideration**:
- Docker socket access = root privileges
- Use read-only mount: `/var/run/docker.sock:ro`
- In production, consider rootless Docker or API-based discovery

### 2.3 Docker Compose Configuration

**File**: `monitoring/docker-compose.yml`

**Key Design Decisions**:

#### Loki Service
```yaml
loki:
  image: grafana/loki:3.0.0
  command: -config.file=/etc/loki/config.yml
  volumes:
    - ./loki/config.yml:/etc/loki/config.yml:ro
    - loki-data:/tmp/loki
  ports:
    - "3100:3100"
```

**Why These Choices**:
- **Version 3.0.0**: Latest stable with TSDB support
- **Config Mount**: Read-only for security
- **Data Volume**: Persistent storage for logs
- **Port 3100**: Standard Loki HTTP port

#### Promtail Service
```yaml
promtail:
  image: grafana/promtail:3.0.0
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
  depends_on:
    loki:
      condition: service_healthy
```

**Why These Choices**:
- **Docker Socket**: For container discovery
- **Container Logs**: Direct access to Docker log files
- **Read-Only**: Security best practice
- **Health Dependency**: Wait for Loki before starting

#### Grafana Service
```yaml
grafana:
  image: grafana/grafana:11.3.1
  environment:
    - GF_AUTH_ANONYMOUS_ENABLED=true  # DEV ONLY
    - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
  volumes:
    - grafana-data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning:ro
```

**Why These Choices**:
- **Anonymous Auth**: For testing convenience (remove in production!)
- **Provisioning**: Auto-configure Loki datasource
- **Persistent Data**: Dashboards and settings survive restarts

### 2.4 Loki Configuration Deep Dive

**File**: `monitoring/loki/config.yml`

#### TSDB Storage Configuration

```yaml
schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13
```

**TSDB Benefits (Loki 3.0+)**:
- **10x Query Performance**: Optimized index structure
- **Lower Memory**: More efficient than boltdb-shipper
- **Better Compression**: Smaller storage footprint
- **Faster Compaction**: Quicker cleanup operations

**Schema v13**:
- Required for TSDB
- Incompatible with older schemas (migration needed)
- Standard for Loki 3.0+

#### Retention Configuration

```yaml
limits_config:
  retention_period: 168h  # 7 days

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
  compaction_interval: 10m
```

**How Retention Works**:
1. **Mark**: Compactor marks logs older than 168h
2. **Wait**: Delay 2h before deletion (safety buffer)
3. **Delete**: Remove marked logs from storage
4. **Compact**: Clean up index and chunks

**Why 7 Days**:
- Balances storage cost vs. debugging needs
- Sufficient for most incident investigations
- Can be extended to 30+ days for compliance

### 2.5 Promtail Configuration Deep Dive

**File**: `monitoring/promtail/config.yml`

#### Pipeline Stages

```yaml
pipeline_stages:
  - json:
      expressions:
        level: level
        timestamp: timestamp
        message: message
        method: method
        path: path
        status_code: status_code
```

**Pipeline Processing**:
1. **JSON Parser**: Extract fields from JSON logs
2. **Labels Extraction**: Convert fields to Loki labels
3. **Timestamp Parsing**: Use log timestamp, not ingestion time
4. **Output Stage**: Optional debugging output

**Why JSON Parsing**:
- Structured data is easier to query
- Extract specific fields: `| json | level="ERROR"`
- Performance: No regex parsing needed
- Consistency: Same format across all apps

#### Label Extraction

```yaml
- labels:
    level:
    method:
```

**Careful Label Selection**:
- **level**: Low cardinality (INFO, ERROR, DEBUG)
- **method**: Low cardinality (GET, POST, PUT, DELETE)
- **status_code**: Medium cardinality (200, 404, 500...)
- **path**: High cardinality (unique URLs)

**Trade-off**: More labels = easier queries but worse performance

### 2.6 Deployment and Verification

#### Deploy the Stack

```bash
cd monitoring

# Create .env file (see section 2.7)
cp .env.example .env
# Edit .env and set GRAFANA_ADMIN_PASSWORD

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f loki
docker compose logs -f promtail
```

**Expected Output**:
```
NAME                STATUS              PORTS
loki                healthy             0.0.0.0:3100->3100/tcp
promtail            healthy             0.0.0.0:9080->9080/tcp
grafana             healthy             0.0.0.0:3000->3000/tcp
devops-python-app   healthy             0.0.0.0:8000->5000/tcp
```

#### Verify Loki

```bash
# Check readiness
curl http://localhost:3100/ready
# Expected: Ready

# Check metrics
curl http://localhost:3100/metrics | grep loki

# Check config
curl http://localhost:3100/config | jq .
```

#### Verify Promtail

```bash
# Check targets
curl http://localhost:9080/targets | jq .

# Expected output:
# {
#   "activeTargets": [
#     {
#       "labels": {
#         "app": "devops-python",
#         "container": "devops-python-app",
#         "job": "docker"
#       },
#       "discoveredLabels": { ... }
#     }
#   ]
# }

# Check metrics
curl http://localhost:9080/metrics | grep promtail
```

#### Verify Grafana

1. **Access Grafana**: http://localhost:3000
   - Default login: `admin` / `admin` (or your .env password)
   
2. **Check Datasource**:
   - Go to **Connections** -> **Data sources**
   - Should see "Loki" with green checkmark
   - If not: Add manually with URL `http://loki:3100`

3. **Test in Explore**:
   - Click **Explore** (compass icon)
   - Select **Loki** datasource
   - Query: `{job="docker"}`
   - Should see logs from all containers

### 2.7 Environment Configuration

**File**: `monitoring/.env`

**Step-by-Step**:
```bash
cd monitoring
cp .env.example .env
```

**Edit `.env` and change**:
```bash
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password_here
```

## 3. Task 2 — Integrate Applications (3 pts)

### 3.1 JSON Logging Implementation

**Library Choice**: `python-json-logger` (version 3.2.1)

**Why python-json-logger**:
- **Maintained**: Active development and updates
- **Simple**: Extends standard `logging.Formatter`
- **Flexible**: Customizable JSON fields
- **Compatible**: Works with any logging handler

**Alternative Considered**: `structlog`
- More powerful but heavier
- Overkill for this use case
- Steeper learning curve

#### Custom JSON Formatter

**File**: `app_python/app.py` (lines 10-18)

```python
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
```

**Custom Fields Added**:
- `timestamp`: ISO 8601 format with timezone
- `level`: INFO, ERROR, DEBUG, WARNING
- `logger`: Logger name (devops-info-service)
- `module`: Source module (app, controller, etc.)
- `function`: Function that logged the message

**Why These Fields**:
- **Timestamp**: Critical for time-series analysis
- **Level**: Easy filtering in Grafana
- **Context**: Debug where log originated

#### Logging Setup

```python
logger = logging.getLogger("devops-info-service")
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

json_handler = logging.StreamHandler(sys.stdout)
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
json_handler.setFormatter(formatter)
logger.addHandler(json_handler)
```

**Configuration**:
- **Stream**: `sys.stdout` (Docker captures this)
- **Log Level**: Configurable via `LOG_LEVEL` env var
- **Format**: JSON with custom fields

### 3.2 Request/Response Logging

#### Middleware Implementation

**File**: `app_python/app.py` (lines 51-71)

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    # Log incoming request
    logger.info("HTTP Request", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get('user-agent', 'unknown')
    })
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info("HTTP Response", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code
    })
    
    return response
```

**What's Logged**:
- **Request**: Method, path, client IP, user agent
- **Response**: Method, path, status code
- **Extra Fields**: Merged into JSON output

**Example Log Output**:
```json
{
  "timestamp": "2026-03-12T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "devops-info-service",
  "module": "app",
  "function": "log_requests",
  "message": "HTTP Request",
  "method": "GET",
  "path": "/",
  "client_ip": "172.18.0.1",
  "user_agent": "curl/7.88.1"
}
```

### 3.3 Application Startup Logging

```python
logger.info("Application starting", extra={
    "host": HOST,
    "port": PORT,
    "debug": DEBUG,
    "python_version": platform.python_version()
})
```

**Why Log Startup**:
- Confirms app is running
- Shows configuration values
- Useful for debugging deployment issues

### 3.4 Docker Compose Integration

**Application Service in `monitoring/docker-compose.yml`**:

```yaml
app-python:
  build:
    context: ../app_python
    dockerfile: Dockerfile
  container_name: devops-python-app
  ports:
    - "8000:5000"
  environment:
    - PORT=5000
    - DEBUG=false
    - LOG_LEVEL=INFO
  networks:
    - logging
  labels:
    logging: "promtail"
    app: "devops-python"
  healthcheck:
    test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
  restart: unless-stopped
  depends_on:
    promtail:
      condition: service_healthy
```

**Key Configuration**:
- **Labels**: `logging=promtail` and `app=devops-python`
  - Promtail filters by `logging=promtail`
  - `app` label appears in Loki queries
- **Environment**: `LOG_LEVEL=INFO` for production-like logging
- **Network**: Joins `logging` network
- **Health Check**: Verifies app is responding
- **Dependencies**: Waits for Promtail to be healthy

### 3.5 Generate Test Logs

**Script**: Create `monitoring/test-logs.sh` (if needed)

```bash
#!/bin/bash
echo "Generating test traffic..."

# Generate successful requests
for i in {1..20}; do
  curl -s http://localhost:8000/ > /dev/null
  echo "Request $i to /"
done

# Generate health checks
for i in {1..20}; do
  curl -s http://localhost:8000/health > /dev/null
  echo "Request $i to /health"
done

# Generate errors (404)
for i in {1..10}; do
  curl -s http://localhost:8000/nonexistent > /dev/null
  echo "Request $i to /nonexistent (404)"
done

echo "Test traffic generated"
```

**Run**:
```bash
cd monitoring
bash test-logs.sh
```

### 3.6 Verify Logs in Grafana

**Evidence Required - Manual Steps**:

1. **Open Grafana**: http://localhost:3000

2. **Navigate to Explore**:
   - Click **Explore** icon (compass) in left sidebar
   - Select **Loki** datasource from dropdown

3. **Query All App Logs**:
   ```logql
   {app="devops-python"}
   ```

4. **Query by Log Level**:
   ```logql
   {app="devops-python"} | json | level="INFO"
   ```

5. **Query HTTP Requests**:
   ```logql
   {app="devops-python"} | json | method="GET"
   ```

6. **Query Errors** (if any):
   ```logql
   {app="devops-python"} |= "ERROR"
   ```

---

## 4. Task 3 — Build Log Dashboard (2 pts)

### 4.1 LogQL Query Examples

#### Basic Queries

**1. All logs from app**:
```logql
{app="devops-python"}
```

**2. Filter by container**:
```logql
{container="devops-python-app"}
```

**3. Multiple apps**:
```logql
{app=~"devops-.*"}
```

**4. Specific job**:
```logql
{job="docker"}
```

#### Text Filtering

**5. Contains "error" (case-insensitive)**:
```logql
{app="devops-python"} |= "error"
```

**6. Doesn't contain "health"**:
```logql
{app="devops-python"} != "health"
```

**7. Regex match**:
```logql
{app="devops-python"} |~ "status_code\":\\s*[45]\\d\\d"
```

#### JSON Parsing

**8. Parse JSON and filter**:
```logql
{app="devops-python"} | json | level="ERROR"
```

**9. Multiple field filters**:
```logql
{app="devops-python"} | json | method="GET" | status_code="200"
```

**10. Numeric comparison** (Loki 3.0+):
```logql
{app="devops-python"} | json | unwrap status_code | status_code >= 400
```

#### Metrics from Logs

**11. Logs per second**:
```logql
rate({app="devops-python"}[1m])
```

**12. Count by level**:
```logql
sum by (level) (count_over_time({app="devops-python"} | json [5m]))
```

**13. Request rate by method**:
```logql
sum by (method) (rate({app="devops-python"} | json | message="HTTP Request" [1m]))
```

**14. Error rate**:
```logql
sum(rate({app="devops-python"} | json | level="ERROR" [5m]))
```

**15. 95th percentile response time** (if logged):
```logql
quantile_over_time(0.95, {app="devops-python"} | json | unwrap response_time [5m])
```

### 4.2 Dashboard Creation Guide

**Manual Steps Required - Follow This Guide**:

#### Panel 1: Logs Table

1. **Grafana** -> **Dashboards** -> **New** -> **New Dashboard**
2. **Add visualization**
3. **Panel settings**:
   - **Title**: "Application Logs"
   - **Data source**: Loki
   - **Query**:
     ```logql
     {app=~"devops-.*"} | json
     ```
   - **Visualization**: Logs
   - **Options**:
     - Show time: +
     - Wrap lines: +
     - Pretty print: +
     - Deduplication: None
4. **Apply** and **Save**

#### Panel 2: Request Rate (Time Series)

1. **Add panel** -> **Add visualization**
2. **Panel settings**:
   - **Title**: "Logs per Second by Application"
   - **Data source**: Loki
   - **Query**:
     ```logql
     sum by (app) (rate({app=~"devops-.*"} [1m]))
     ```
   - **Visualization**: Time series
   - **Options**:
     - Legend: {{app}}
     - Unit: logs/s
     - Draw style: Lines
3. **Apply**

#### Panel 3: Error Logs

1. **Add panel** -> **Add visualization**
2. **Panel settings**:
   - **Title**: "Error Logs Only"
   - **Data source**: Loki
   - **Query**:
     ```logql
     {app=~"devops-.*"} | json | level="ERROR"
     ```
   - **Visualization**: Logs
   - **Options**:
     - Highlight errors: +
3. **Apply**

#### Panel 4: Log Level Distribution

1. **Add panel** -> **Add visualization**
2. **Panel settings**:
   - **Title**: "Log Levels Distribution"
   - **Data source**: Loki
   - **Query**:
     ```logql
     sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
     ```
   - **Visualization**: Pie chart (or Stat)
   - **Options**:
     - Legend: {{level}}
     - Show values: Percent
3. **Apply**

#### Panel 5: HTTP Methods (Bonus)

1. **Add panel** -> **Add visualization**
2. **Panel settings**:
   - **Title**: "HTTP Methods"
   - **Data source**: Loki
   - **Query**:
     ```logql
     sum by (method) (count_over_time({app="devops-python"} | json | method!="" [5m]))
     ```
   - **Visualization**: Bar chart
3. **Apply**

#### Save Dashboard

1. **Click Save dashboard** (disk icon)
2. **Name**: "Application Logs Dashboard"
3. **Folder**: General
4. **Save**

### 4.3 Dashboard Best Practices

**Layout**:
- Put most important panel at top-left (users scan F-pattern)
- Group related panels together
- Use consistent time ranges

**Performance**:
- Avoid queries with high-cardinality labels
- Use time range limits (`[5m]` instead of `[24h]`)
- Add panel caching where appropriate

**Usability**:
- Add panel descriptions
- Use meaningful titles
- Include units on axes
- Add thresholds and alerts

## 5. Task 4 — Production Readiness (1 pt)

### 5.1 Resource Limits

**Already Implemented** in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Limits by Service**:

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| Loki | 1.0 | 1 GB | 0.5 | 512 MB |
| Promtail | 0.5 | 512 MB | 0.25 | 256 MB |
| Grafana | 1.0 | 1 GB | 0.5 | 512 MB |
| Python App | 0.5 | 512 MB | 0.25 | 256 MB |

**Why These Values**:
- **Loki**: Needs memory for index caching
- **Promtail**: Lightweight, minimal resources
- **Grafana**: UI requires more memory for dashboards
- **Python App**: Small FastAPI app, minimal needs

**Reservations**:
- Guarantees minimum resources
- Prevents starvation under load
- Allows bursting up to limits

### 5.2 Security Configuration

#### Grafana Authentication

**Development Configuration** (current):
```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=true
  - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
```

**For Production** (change to):
```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
```

**Steps to Secure**:
1. Edit `docker-compose.yml`
2. Change `GF_AUTH_ANONYMOUS_ENABLED=false`
3. Set strong password in `.env`
4. Restart Grafana: `docker compose restart grafana`

#### Docker Socket Security

**Current** (read-only mount):
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

**Security Risk**:
- Docker socket = root access to host
- Compromised Promtail = full system access

**Mitigation Options**:
1. **Docker Socket Proxy**: Use `tecnativa/docker-socket-proxy`
2. **Rootless Docker**: Run Docker as non-root user
3. **Alternative**: Use Docker API with TLS authentication
4. **Container Isolation**: Run Promtail with limited capabilities

**For This Lab**: Read-only mount is acceptable for learning
**For Production**: Implement proper socket isolation

### 5.3 Health Checks

**Already Implemented** for all services:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**Parameters Explained**:
- **test**: Command to check health
- **interval**: Check every 10 seconds
- **timeout**: Fail if no response in 5 seconds
- **retries**: Mark unhealthy after 5 failures
- **start_period**: Grace period during startup

**Health Endpoints**:
- **Loki**: `http://localhost:3100/ready`
- **Promtail**: `http://localhost:9080/ready`
- **Grafana**: `http://localhost:3000/api/health`
- **Python App**: `http://localhost:5000/health`

**Dependency Order**:
```
Loki (healthy) -> Promtail (healthy) -> Python App
    ↓
  Grafana
```

**Verify Health**:
```bash
docker compose ps

# Expected output:
# NAME                STATUS              
# loki                Up 2 minutes (healthy)
# promtail            Up 2 minutes (healthy)
# grafana             Up 2 minutes (healthy)
# devops-python-app   Up 2 minutes (healthy)
```

### 5.4 Additional Production Considerations

#### Backup and Recovery

**What to Backup**:
- Loki data: `loki-data` volume
- Grafana data: `grafana-data` volume (dashboards, users)
- Configuration files: `loki/config.yml`, `promtail/config.yml`

**Backup Strategy**:
```bash
# Backup volumes
docker run --rm \
  -v loki-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/loki-data.tar.gz /data

# Restore
docker run --rm \
  -v loki-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/loki-data.tar.gz -C /
```

#### Monitoring the Monitoring Stack

**Monitor**:
- Disk usage: Loki data volume
- Memory usage: All services
- Log ingestion rate: Promtail metrics
- Query performance: Loki metrics

**Export Metrics**:
- Loki exposes Prometheus metrics on `:3100/metrics`
- Promtail exposes metrics on `:9080/metrics`
- Grafana exposes metrics on `:3000/metrics`

**Set Alerts**:
- Disk > 80% full
- Loki ingestion errors
- Promtail targets down

#### Network Security

**Current**: Bridge network (internal communication)
```yaml
networks:
  logging:
    driver: bridge
```

**For Production**:
- Use overlay network for multi-host
- Implement network policies
- Enable TLS between services
- Use secrets for credentials


## 6. Task 5 — Documentation (2 pts)

### 6.1 Architecture Diagram

See section 1.2 for complete architecture diagram.

**Components**:
- Docker containers writing JSON logs
- Promtail collecting via Docker socket
- Loki storing with TSDB
- Grafana visualizing logs

### 6.2 Setup Guide

**Prerequisites**:
- Docker Engine 20.10+
- Docker Compose v2 (with `docker compose` command)
- 4 GB RAM minimum
- 10 GB disk space

**Step-by-Step Deployment**:

```bash
# 1. Clone repository
cd DevOps-Core-Course

# 2. Navigate to monitoring directory
cd monitoring

# 3. Create .env file
cp .env.example .env
# Edit .env and set GRAFANA_ADMIN_PASSWORD

# 4. Start stack
docker compose up -d

# 5. Verify services
docker compose ps
# All services should show "healthy"

# 6. Check logs
docker compose logs -f

# 7. Access Grafana
# Open http://localhost:3000
# Login with admin / your_password

# 8. Verify Loki datasource
# Go to Connections -> Data sources -> Loki
# Should show "Data source is working"

# 9. Explore logs
# Click Explore -> Select Loki
# Query: {job="docker"}

# 10. Generate test traffic
curl http://localhost:8000/
curl http://localhost:8000/health

# 11. Create dashboard (follow Task 3 guide)
```

**Teardown**:
```bash
# Stop services
docker compose down

# Remove volumes (deletes all data)
docker compose down -v

# Remove images
docker compose down --rmi all
```

### 6.3 Configuration Explanation

**Loki Config Highlights**:
- **TSDB**: Faster than boltdb-shipper
- **Retention**: 168h (7 days)
- **Compactor**: Cleans up old logs automatically
- **Schema v13**: Required for Loki 3.0+

**Promtail Config Highlights**:
- **Docker SD**: Auto-discovers containers
- **Label Filter**: Only `logging=promtail`
- **JSON Parser**: Extracts structured fields
- **Relabeling**: Creates meaningful labels

**Grafana Config Highlights**:
- **Provisioning**: Auto-configures Loki datasource
- **Anonymous Auth**: Enabled for development (disable for prod)
- **Persistent Storage**: Dashboards saved to volume

### 6.4 Application Logging Design

**JSON Logging**:
- Library: `python-json-logger`
- Custom formatter with timestamp, level, context
- HTTP middleware logs every request/response
- Startup logging with configuration details

**Log Levels**:
- **INFO**: Normal operations (requests, startup)
- **ERROR**: Exceptions and errors
- **DEBUG**: Detailed debugging (disabled by default)
- **WARNING**: Non-critical issues

**Logged Events**:
- Application startup with config
- Every HTTP request (method, path, IP, user agent)
- Every HTTP response (status code, method, path)
- Application errors and exceptions

### 6.5 Dashboard Explanation

**Panel 1: Logs Table**
- **Purpose**: View raw logs from all apps
- **Query**: `{app=~"devops-.*"} | json`
- **Use**: Quick log inspection, debugging

**Panel 2: Request Rate**
- **Purpose**: Monitor traffic volume
- **Query**: `sum by (app) (rate({app=~"devops-.*"} [1m]))`
- **Use**: Detect traffic spikes, unusual patterns

**Panel 3: Error Logs**
- **Purpose**: Focus on failures
- **Query**: `{app=~"devops-.*"} | json | level="ERROR"`
- **Use**: Incident response, error tracking

**Panel 4: Log Level Distribution**
- **Purpose**: Understand log composition
- **Query**: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- **Use**: Detect unusual error rates

### 6.6 Testing Commands

**Test Loki**:
```bash
# Check ready status
curl http://localhost:3100/ready

# Query API
curl http://localhost:3100/loki/api/v1/labels

# Get label values
curl http://localhost:3100/loki/api/v1/label/app/values

# Run query
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={app="devops-python"}' \
  | jq .
```

**Test Promtail**:
```bash
# Check targets
curl http://localhost:9080/targets | jq .

# Check metrics
curl http://localhost:9080/metrics | grep promtail_targets_active_total
```

**Test Application Logs**:
```bash
# Generate traffic
for i in {1..50}; do curl -s http://localhost:8000/ > /dev/null; done

# Check container logs
docker logs devops-python-app | tail -20

# Should see JSON output
```

**Test Grafana**:
```bash
# Check health
curl http://localhost:3000/api/health

# Check datasources (requires auth)
curl -u admin:your_password http://localhost:3000/api/datasources
```

## 6. Bonus — Ansible Automation (2.5 pts)

### 6.1 Ansible Role Structure

**Role Path**: `ansible/roles/monitoring`

```
roles/monitoring/
├── defaults/
│   └── main.yml              # Default variables
├── tasks/
│   ├── main.yml              # Main orchestration
│   ├── setup.yml             # Directory and config setup
│   └── deploy.yml            # Docker Compose deployment
├── templates/
│   ├── docker-compose.yml.j2 # Templated compose file
│   ├── loki-config.yml.j2    # Templated Loki config
│   ├── promtail-config.yml.j2 # Templated Promtail config
│   └── env.j2                # Templated .env file
├── handlers/
│   └── main.yml              # Service restart handlers
└── meta/
    └── main.yml              # Role dependencies
```

### 6.2 Role Variables

**File**: `ansible/roles/monitoring/defaults/main.yml`

```yaml
---
# Monitoring Stack Configuration

# Service versions
loki_version: "3.0.0"
promtail_version: "3.0.0"
grafana_version: "11.3.1"

# Service ports
loki_port: 3100
grafana_port: 3000
promtail_port: 9080

# Loki configuration
loki_retention_period: "168h"  # 7 days
loki_schema_version: "v13"
loki_compaction_interval: "10m"

# Resource limits
loki_memory_limit: "1G"
loki_cpu_limit: "1.0"
grafana_memory_limit: "1G"
grafana_cpu_limit: "1.0"
promtail_memory_limit: "512M"
promtail_cpu_limit: "0.5"

# Grafana configuration
grafana_admin_user: "admin"
grafana_admin_password: "{{ vault_grafana_password | default('changeme') }}"
grafana_anonymous_enabled: false  # Secure by default

# Deployment paths
monitoring_dir: "/opt/monitoring"
monitoring_config_dir: "{{ monitoring_dir }}/config"

# Application configuration
python_app_enabled: true
python_app_port: 8000
python_app_log_level: "INFO"
```

### 6.3 Role Tasks

**File**: `ansible/roles/monitoring/tasks/main.yml`

```yaml
---
# Main orchestration for monitoring stack

- name: Include setup tasks
  include_tasks: setup.yml
  tags:
    - setup
    - monitoring

- name: Include deployment tasks
  include_tasks: deploy.yml
  tags:
    - deploy
    - monitoring
```

**File**: `ansible/roles/monitoring/tasks/setup.yml`

```yaml
---
# Setup tasks: directories and configuration files

- name: Create monitoring directories
  file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
  loop:
    - "{{ monitoring_dir }}"
    - "{{ monitoring_dir }}/loki"
    - "{{ monitoring_dir }}/promtail"
    - "{{ monitoring_dir }}/grafana"
    - "{{ monitoring_dir }}/grafana/provisioning"
    - "{{ monitoring_dir }}/grafana/provisioning/datasources"
    - "{{ monitoring_dir }}/docs"

- name: Template Loki configuration
  template:
    src: loki-config.yml.j2
    dest: "{{ monitoring_dir }}/loki/config.yml"
    mode: '0644'
  notify: Restart monitoring stack

- name: Template Promtail configuration
  template:
    src: promtail-config.yml.j2
    dest: "{{ monitoring_dir }}/promtail/config.yml"
    mode: '0644'
  notify: Restart monitoring stack

- name: Template Grafana Loki datasource
  copy:
    content: |
      apiVersion: 1
      datasources:
        - name: Loki
          type: loki
          access: proxy
          url: http://loki:{{ loki_port }}
          isDefault: true
          editable: true
    dest: "{{ monitoring_dir }}/grafana/provisioning/datasources/loki.yml"
    mode: '0644'

- name: Template Docker Compose file
  template:
    src: docker-compose.yml.j2
    dest: "{{ monitoring_dir }}/docker-compose.yml"
    mode: '0644'
  notify: Restart monitoring stack

- name: Template environment file
  template:
    src: env.j2
    dest: "{{ monitoring_dir }}/.env"
    mode: '0600'  # Secure: only owner can read
  no_log: true  # Don't log passwords
```

**File**: `ansible/roles/monitoring/tasks/deploy.yml`

```yaml
---
# Deployment tasks: Docker Compose

- name: Check if Docker is installed
  command: docker --version
  register: docker_check
  changed_when: false
  failed_when: false

- name: Fail if Docker is not installed
  fail:
    msg: "Docker is not installed. Please run the docker role first."
  when: docker_check.rc != 0

- name: Deploy monitoring stack with Docker Compose
  community.docker.docker_compose_v2:
    project_src: "{{ monitoring_dir }}"
    state: present
    pull: policy
  register: compose_result

- name: Wait for Loki to be ready
  uri:
    url: "http://localhost:{{ loki_port }}/ready"
    method: GET
    status_code: 200
  retries: 30
  delay: 2
  register: loki_ready
  until: loki_ready.status == 200

- name: Wait for Promtail to be ready
  uri:
    url: "http://localhost:{{ promtail_port }}/ready"
    method: GET
    status_code: 200
  retries: 20
  delay: 2
  register: promtail_ready
  until: promtail_ready.status == 200

- name: Wait for Grafana to be ready
  uri:
    url: "http://localhost:{{ grafana_port }}/api/health"
    method: GET
    status_code: 200
  retries: 30
  delay: 2
  register: grafana_ready
  until: grafana_ready.status == 200

- name: Display deployment status
  debug:
    msg: |
      Monitoring stack deployed successfully!
      
      Access URLs:
      - Grafana: http://{{ ansible_default_ipv4.address }}:{{ grafana_port }}
      - Loki: http://{{ ansible_default_ipv4.address }}:{{ loki_port }}
      - Promtail: http://{{ ansible_default_ipv4.address }}:{{ promtail_port }}
      
      Credentials:
      - Username: {{ grafana_admin_user }}
      - Password: (stored in .env)
```

### 6.4 Templates

**File**: `ansible/roles/monitoring/templates/docker-compose.yml.j2`

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:{{ loki_version }}
    container_name: loki
    ports:
      - "{{ loki_port }}:3100"
    command: -config.file=/etc/loki/config.yml
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro
      - loki-data:/tmp/loki
    networks:
      - logging
    deploy:
      resources:
        limits:
          cpus: '{{ loki_cpu_limit }}'
          memory: {{ loki_memory_limit }}
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  promtail:
    image: grafana/promtail:{{ promtail_version }}
    container_name: promtail
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./promtail/config.yml:/etc/promtail/config.yml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    networks:
      - logging
    depends_on:
      loki:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '{{ promtail_cpu_limit }}'
          memory: {{ promtail_memory_limit }}
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9080/ready || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  grafana:
    image: grafana/grafana:{{ grafana_version }}
    container_name: grafana
    ports:
      - "{{ grafana_port }}:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED={{ 'true' if grafana_anonymous_enabled else 'false' }}
{% if grafana_anonymous_enabled %}
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
{% endif %}
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_SERVER_ROOT_URL=http://localhost:{{ grafana_port }}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - logging
    depends_on:
      loki:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '{{ grafana_cpu_limit }}'
          memory: {{ grafana_memory_limit }}
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

{% if python_app_enabled %}
  app-python:
    build:
      context: ../app_python
      dockerfile: Dockerfile
    container_name: devops-python-app
    ports:
      - "{{ python_app_port }}:5000"
    environment:
      - PORT=5000
      - LOG_LEVEL={{ python_app_log_level }}
    networks:
      - logging
    labels:
      logging: "promtail"
      app: "devops-python"
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    depends_on:
      promtail:
        condition: service_healthy
{% endif %}

networks:
  logging:
    driver: bridge

volumes:
  loki-data:
  grafana-data:
```

**File**: `ansible/roles/monitoring/templates/loki-config.yml.j2`

```yaml
# Loki {{ loki_version }} Configuration
# Generated by Ansible

auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: {{ loki_schema_version }}
      index:
        prefix: index_
        period: 24h

storage_config:
  tsdb_shipper:
    active_index_directory: /tmp/loki/tsdb-index
    cache_location: /tmp/loki/tsdb-cache
    cache_ttl: 24h
  filesystem:
    directory: /tmp/loki/chunks

compactor:
  working_directory: /tmp/loki/boltdb-shipper-compactor
  shared_store: filesystem
  compaction_interval: {{ loki_compaction_interval }}
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

limits_config:
  retention_period: {{ loki_retention_period }}
  reject_old_samples: true
  reject_old_samples_max_age: {{ loki_retention_period }}
  ingestion_rate_mb: 4
  ingestion_burst_size_mb: 6

analytics:
  reporting_enabled: false
```

**File**: `ansible/roles/monitoring/templates/promtail-config.yml.j2`

```yaml
# Promtail {{ promtail_version }} Configuration
# Generated by Ansible

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:{{ loki_port }}/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_app']
        target_label: 'app'
      - replacement: 'docker'
        target_label: 'job'

    pipeline_stages:
      - json:
          expressions:
            level: level
            timestamp: timestamp
            message: message
            method: method
            path: path
            status_code: status_code
      - labels:
          level:
          method:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
          fallback_formats:
            - RFC3339
```

**File**: `ansible/roles/monitoring/templates/env.j2`

```bash
# Environment variables for Monitoring Stack
# Generated by Ansible - DO NOT EDIT MANUALLY

GRAFANA_ADMIN_USER={{ grafana_admin_user }}
GRAFANA_ADMIN_PASSWORD={{ grafana_admin_password }}
```

### 7.5 Handlers

**File**: `ansible/roles/monitoring/handlers/main.yml`

```yaml
---
- name: Restart monitoring stack
  community.docker.docker_compose_v2:
    project_src: "{{ monitoring_dir }}"
    state: restarted
```

### 6.6 Meta Dependencies

**File**: `ansible/roles/monitoring/meta/main.yml`

```yaml
---
dependencies:
  - role: docker
    when: docker_install | default(true)

galaxy_info:
  author: Selivanov George
  description: Ansible role for deploying Loki monitoring stack
  company: Innopolis University
  license: MIT
  min_ansible_version: "2.16"
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
    - name: Debian
      versions:
        - bullseye
        - bookworm
  galaxy_tags:
    - loki
    - grafana
    - monitoring
    - logging
    - observability
```

### 6.7 Deployment Playbook

**File**: `ansible/playbooks/deploy-monitoring.yml`

```yaml
---
- name: Deploy Loki Monitoring Stack
  hosts: all
  become: true
  vars:
    # Override defaults here
    grafana_anonymous_enabled: false
    loki_retention_period: "168h"
    python_app_enabled: true
    
  roles:
    - role: monitoring
      tags:
        - monitoring
        - loki

  post_tasks:
    - name: Display access information
      debug:
        msg: |
          ========================================
          Monitoring Stack Deployed Successfully!
          ========================================
          
          Services:
          - Grafana: http://{{ ansible_default_ipv4.address }}:{{ grafana_port }}
          - Loki API: http://{{ ansible_default_ipv4.address }}:{{ loki_port }}
          - Promtail: http://{{ ansible_default_ipv4.address }}:{{ promtail_port }}
          
          Credentials:
          - Username: {{ grafana_admin_user }}
          - Password: (check .env file on target host)
          
          Next Steps:
          1. Access Grafana and verify Loki datasource
          2. Navigate to Explore and query logs: {job="docker"}
          3. Create dashboards based on Lab 7 requirements
          
          ========================================
```

### 6.8 Variables for Group Vars

**File**: `ansible/group_vars/all.yml` (add these)

```yaml
# Monitoring Stack Configuration
monitoring_stack_enabled: true
loki_version: "3.0.0"
promtail_version: "3.0.0"
grafana_version: "11.3.1"

# Security: Use Ansible Vault for passwords
vault_grafana_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          # ... encrypted password ...

# Or use plain text for development (NOT RECOMMENDED)
# grafana_admin_password: "secure_password_here"
```

### 6.9 Usage Instructions

**Deploy Monitoring Stack**:

```bash
cd ansible

# Run playbook
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml

# With vault password
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --ask-vault-pass

# Dry run (check mode)
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --check

# Only setup tasks
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --tags setup

# Only deployment tasks
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --tags deploy
```

**Test Idempotency**:

```bash
# Run twice
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml
# First run: changed > 0
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml
# Second run: changed = 0 (idempotent)
```

**Expected Output** (first run):
```
PLAY RECAP *************************************************************
localhost : ok=15   changed=10   unreachable=0    failed=0    skipped=0
```

**Expected Output** (second run - idempotent):
```
PLAY RECAP *************************************************************
localhost : ok=15   changed=0    unreachable=0    failed=0    skipped=0
```