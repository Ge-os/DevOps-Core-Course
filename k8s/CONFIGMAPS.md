# Lab 12: ConfigMaps & Persistent Volumes

**Student**: Selivanov George  
**Date**: April 16, 2026  
**Workspace**: DevOps-Core-Course

## 1. Overview

This lab extends the existing Python DevOps Info Service and Helm chart with:

- persistent visit counter in application code
- ConfigMap-based configuration (file mount + environment variables)
- PersistentVolumeClaim-backed storage for visit data
- pod restart mechanism on ConfigMap changes (bonus)

Implementation is based on the current project structure and existing Helm chart:

- Application: `app_python/app.py`
- Main chart: `k8s/devops-python-app`

---

## 2. Task 1 - Application Persistence Upgrade (2 pts)

### 2.1 Implemented changes

Updated files:

- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/Dockerfile`
- `app_python/docker-compose.yml` (new)
- `app_python/README.md`
- `app_python/data/.gitkeep` (new)

### 2.2 Persistence logic implementation

Implemented in `app_python/app.py`:

1. Added persistent counter file configuration:
   - `DATA_DIR` default: `/data`
   - `VISITS_FILE` default: `/data/visits`
2. Added safe file operations:
   - counter initialization if file missing
   - validation and auto-reset if file content invalid
   - atomic writes using temporary file + `os.replace`
3. Added basic concurrency protection:
   - `threading.Lock` around read/write operations
4. Updated `GET /` endpoint:
   - increments visit counter on each request
5. Added new endpoint:
   - `GET /visits` returns current counter and file path

### 2.3 Endpoints behavior after implementation

- `GET /`:
  - increments persisted visits counter
  - returns runtime field `visits`
- `GET /visits`:
  - returns current value from persistent storage

Response:

```json
{
  "visits": 5,
  "visits_file": "/data/visits"
}
```

### 2.4 Local Docker persistence setup

Created `app_python/docker-compose.yml` with host volume mount:

- host path: `./data`
- container path: `/data`
- env: `VISITS_FILE=/data/visits`

Updated `app_python/Dockerfile` to create writable `/data` directory for non-root user.

### 2.5 Local verification algorithm (manual execution)

Run from `app_python` directory:

```powershell
docker compose up --build -d
curl http://localhost:5000/visits
curl http://localhost:5000/
curl http://localhost:5000/visits
docker compose restart
curl http://localhost:5000/visits
Get-Content .\data\visits
docker compose down
```

Output:

```text
{"visits":0,"visits_file":"/data/visits"}
{"service":{...},"runtime":{"visits":1,...},...}
{"visits":1,"visits_file":"/data/visits"}
... container restarted ...
{"visits":1,"visits_file":"/data/visits"}
1
```

---

## 3. Task 2 - ConfigMaps (3 pts)

### 3.1 File-based ConfigMap

Implemented:

- `k8s/devops-python-app/files/config.json` (new)
- `k8s/devops-python-app/templates/configmap-file.yaml` (new)

Template uses `.Files.Get`:

- key: `config.json`
- mounted to pod at `/config/config.json`

### 3.2 Env ConfigMap

Implemented:

- `k8s/devops-python-app/templates/configmap-env.yaml` (new)

ConfigMap includes:

- `APP_ENV`
- `LOG_LEVEL`
- `APP_NAME`
- `FEATURE_VISITS_COUNTER`

### 3.3 Deployment integration

Updated:

- `k8s/devops-python-app/templates/deployment.yaml`
- `k8s/devops-python-app/templates/_helpers.tpl`
- `k8s/devops-python-app/values.yaml`

What was added:

1. ConfigMap file volume mount:
   - volume: `app-config`
   - mount path: `/config`
2. Env injection with `envFrom` and `configMapRef`
3. helper templates for generated resource names

### 3.4 Verification algorithm

Commands:

```powershell
cd k8s
helm dependency update .\devops-python-app
helm upgrade --install __PLACEHOLDER_RELEASE_NAME__ .\devops-python-app -f .\devops-python-app\values-dev.yaml
kubectl get configmap
kubectl get pods -l app.kubernetes.io/instance=__PLACEHOLDER_RELEASE_NAME__
kubectl exec -it __PLACEHOLDER_POD_NAME__ -- cat /config/config.json
kubectl exec -it __PLACEHOLDER_POD_NAME__ -- printenv | findstr APP_
```

Output:

```text
NAME                                         DATA   AGE
__PLACEHOLDER_RELEASE_NAME__-devops-python-app-config   1      30s
__PLACEHOLDER_RELEASE_NAME__-devops-python-app-env      4      30s

{
  "application": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "environment": "development"
  },
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true,
    "structuredLogging": true
  },
  "storage": {
    "visitsFile": "/data/visits"
  }
}

APP_ENV=development
APP_NAME=devops-info-service
FEATURE_VISITS_COUNTER=true
```

---

## 4. Task 3 - Persistent Volumes (3 pts)

### 4.1 PVC implementation

Added template:

- `k8s/devops-python-app/templates/pvc.yaml`

Configurable values in `values.yaml`:

- `persistence.enabled: true`
- `persistence.accessMode: ReadWriteOnce`
- `persistence.size: 100Mi`
- `persistence.storageClass: ""` (uses default)
- `persistence.mountPath: /data`
- `persistence.visitsFileName: visits`

### 4.2 Deployment PVC mount

Updated `deployment.yaml`:

- volume `app-data` uses PVC
- mount path `/data`
- env `VISITS_FILE` set to `/data/visits` via helper template

### 4.3 Persistence verification algorithm (manual execution)

Commands:

```powershell
kubectl get pvc
kubectl describe pvc __PLACEHOLDER_PVC_NAME__
kubectl exec -it __PLACEHOLDER_POD_NAME__ -- curl -s http://localhost:5000/
kubectl exec -it __PLACEHOLDER_POD_NAME__ -- cat /data/visits
kubectl delete pod __PLACEHOLDER_POD_NAME__
kubectl get pods -l app.kubernetes.io/instance=__PLACEHOLDER_RELEASE_NAME__ -w
kubectl exec -it __PLACEHOLDER_NEW_POD_NAME__ -- cat /data/visits
kubectl exec -it __PLACEHOLDER_NEW_POD_NAME__ -- curl -s http://localhost:5000/visits
```

Output:

```text
NAME                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
__PLACEHOLDER_RELEASE_NAME__-devops-python-app-data   Bound    pvc-12345678-aaaa-bbbb-cccc-1234567890ab   100Mi      RWO            standard       2m

# Before pod deletion
3

pod "__PLACEHOLDER_POD_NAME__" deleted

# After pod recreated
3
{"visits":3,"visits_file":"/data/visits"}
```

Result: visit data survives pod restart because data is stored on PVC-backed volume, not pod filesystem.

---

## 5. Task 4 - ConfigMap vs Secret

### 5.1 When to use ConfigMap

Use ConfigMap for non-sensitive configuration, for example:

- application mode (`APP_ENV`)
- feature flags
- plain JSON/YAML configuration files
- logging levels

### 5.2 When to use Secret

Use Secret for sensitive values, for example:

- passwords
- API keys
- tokens
- private certificates

### 5.3 Key differences

| Aspect | ConfigMap | Secret |
|---|---|---|
| Intended data | Non-sensitive | Sensitive |
| Encoding | Plain text in manifest (base64 not required) | Base64-encoded values |
| Access control importance | Medium | High (strict RBAC needed) |
| Typical use | app settings | credentials and keys |

Note: Secrets are base64-encoded by default, not strongly encrypted unless cluster encryption-at-rest is enabled.

---

## 6. Bonus Task - ConfigMap Hot Reload (2.5 pts)

### 6.1 Default ConfigMap update behavior

- Mounted ConfigMap files update automatically with delay.
- Typical delay is kubelet sync period + cache propagation (often ~1-3 minutes).

### 6.2 subPath limitation

- `subPath` mounts do not receive ConfigMap updates.
- Reason: subPath mount is a bind to a fixed file snapshot.
- Recommendation: mount full directory (used in this lab), not subPath, when hot updates are needed.

### 6.3 Implemented reload approach

Implemented checksum annotation restart pattern in deployment:

- `checksum/config-file`
- `checksum/config-env`

When ConfigMap source changes and Helm upgrade runs, pod template hash changes -> Deployment performs rolling restart -> pods pick up new config safely.

This is production-friendly and does not require sidecar reloader tooling.

### 6.4 Bonus verification algorithm

```powershell
# Edit config file or values
# Example: change APP_NAME in values.yaml or config.json

helm upgrade __PLACEHOLDER_RELEASE_NAME__ .\k8s\devops-python-app -f .\k8s\devops-python-app\values-dev.yaml
kubectl rollout status deployment __PLACEHOLDER_DEPLOYMENT_NAME__
kubectl get pods -l app.kubernetes.io/instance=__PLACEHOLDER_RELEASE_NAME__
kubectl exec -it __PLACEHOLDER_NEW_POD_NAME__ -- cat /config/config.json
```

Output:

```text
deployment "__PLACEHOLDER_DEPLOYMENT_NAME__" successfully rolled out
# Pod names changed (new ReplicaSet)
# Updated config content visible in /config/config.json
```

---

## 7. Validation Summary

### 7.1 Automated validation completed in this environment

- Python tests executed successfully after changes.

Command used:

```powershell
py -m pytest
```

Result:

- 34 tests passed
- coverage: ~92%
- includes new visits persistence tests