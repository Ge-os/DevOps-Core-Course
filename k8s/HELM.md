# Lab 10: Helm Package Manager

**Student**: Selivanov George  
**Date**: April 2, 2026  
**Workspace**: DevOps-Core-Course

## 1. Overview

This lab converts Kubernetes manifests from Lab 9 into reusable Helm charts with:

- full templating and centralized values
- dev/prod environment override files
- lifecycle hooks (pre-install and post-install)
- bonus implementation with library chart reuse across two app charts

The implementation is aligned with existing application behavior:

- app container port remains `5000`
- service port remains `80`
- readiness/liveness probes remain enabled and use `GET /health`
- rollout strategy remains rolling update (`maxSurge: 1`, `maxUnavailable: 0`)

## 2. Task-by-Task Solution

### 2.1 Task 1 - Helm Fundamentals (Implemented + execution steps provided)

Helm concepts applied in this lab:

- **Chart**: Package with templates and defaults (`k8s/devops-python-app`)
- **Release**: Runtime installation instance (example: `myapp-dev`)
- **Repository**: Dependency source, including local file dependency (`file://../common-lib`)
- **Values**: Centralized configuration in `values.yaml` and override files

Environment note:

- Helm CLI is not installed in this agent environment, so command execution evidence is prepared as a step-by-step algorithm with highlighted placeholders for your local run outputs.

### 2.2 Task 2 - Create Helm Chart (Implemented)

Primary chart created:

- `k8s/devops-python-app`

Implemented files:

- `Chart.yaml` with metadata and dependency on `common-lib`
- `values.yaml` with image, replicas, resources, probes, service, env vars
- `templates/deployment.yaml` converted from `k8s/deployment.yml`
- `templates/service.yaml` converted from `k8s/service.yml`
- `templates/_helpers.tpl` (wrapper helpers)

Templated elements:

- image repo/tag/pullPolicy
- replica count
- service type/port/targetPort/nodePort
- resource requests/limits
- readiness/liveness probes (kept active, configurable)
- labels/selectors via helper templates

### 2.3 Task 3 - Multi-Environment Support (Implemented)

Environment override files created in primary chart:

- `k8s/devops-python-app/values-dev.yaml`
- `k8s/devops-python-app/values-prod.yaml`

Differences implemented:

- **Dev**: 1 replica, lower resources, NodePort usage
- **Prod**: 3 replicas, stronger resources, LoadBalancer type, fixed image tag

### 2.4 Task 4 - Chart Hooks (Implemented)

Hook templates added:

- `k8s/devops-python-app/templates/hooks/pre-install-job.yaml`
- `k8s/devops-python-app/templates/hooks/post-install-job.yaml`

Hook configuration:

- `pre-install` with weight `-5`
- `post-install` with weight `5`
- deletion policy: `hook-succeeded,before-hook-creation`
- hook commands and image configurable from values (`hooks.*`)

### 2.5 Task 5 - Documentation (This file)

This document includes:

- chart overview and file structure
- configuration guide
- hook design and behavior
- installation, validation, operations commands
- evidence placeholders to paste your local outputs

### 2.6 Bonus Task - Library Charts (Implemented)

Library chart created:

- `k8s/common-lib`

Second app chart created:

- `k8s/devops-python-app-v2`

Shared templates implemented in library chart:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.selectorLabels`
- `common.labels`

Both app charts depend on and reference the library chart using:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: file://../common-lib
```

## 3. Chart Structure

```text
k8s/
  common-lib/
    Chart.yaml
    values.yaml
    templates/
      _helpers.tpl

  devops-python-app/
    Chart.yaml
    values.yaml
    values-dev.yaml
    values-prod.yaml
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
      NOTES.txt
      hooks/
        pre-install-job.yaml
        post-install-job.yaml

  devops-python-app-v2/
    Chart.yaml
    values.yaml
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
```

## 4. Configuration Guide

### 4.1 Important values (primary chart)

| Key | Purpose | Default |
|---|---|---|
| `replicaCount` | Number of pod replicas | `3` |
| `image.repository` | Docker image repository | `ge0s1/devops-python-app` |
| `image.tag` | Docker image tag | `latest` |
| `service.type` | Service exposure type | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container target port | `5000` |
| `service.nodePort` | Fixed node port for NodePort service | `30080` |
| `resources.*` | CPU and memory requests/limits | from Lab 9 |
| `readinessProbe.*` | Startup/readiness probe policy | enabled |
| `livenessProbe.*` | Health/liveness probe policy | enabled |
| `hooks.enabled` | Enable/disable hook jobs | `true` |
| `hooks.preInstall.*` | Pre-install hook parameters | configured |
| `hooks.postInstall.*` | Post-install hook parameters | configured |

### 4.2 Example installs

```bash
# Build local chart dependencies first
helm dependency update k8s/devops-python-app

# Render locally
helm template myapp k8s/devops-python-app

# Install dev
helm install myapp-dev k8s/devops-python-app -f k8s/devops-python-app/values-dev.yaml

# Install prod
helm install myapp-prod k8s/devops-python-app -f k8s/devops-python-app/values-prod.yaml
```

## 5. Hook Implementation Details

Implemented hooks:

1. **Pre-install hook**
   - resource: Kubernetes Job
   - annotation: `helm.sh/hook: pre-install`
   - weight: `-5` (runs first)
   - use case: preflight validation placeholder

2. **Post-install hook**
   - resource: Kubernetes Job
   - annotation: `helm.sh/hook: post-install`
   - weight: `5` (runs after pre-install and release resources)
   - use case: post-install smoke-check placeholder

Deletion policy behavior:

- `hook-succeeded`: remove successful hook jobs
- `before-hook-creation`: remove previous hook instance before creating a new one

## 6. Execution

Run these steps locally and replace placeholders with your real output.

### 6.1 Install and verify Helm (Windows)

```powershell
# Option A: winget
winget install Helm.Helm

# Option B: Chocolatey
choco install kubernetes-helm
```

### 6.2 Explore a public chart

```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/prometheus
```

### 6.3 Validate local charts

```powershell
# Primary chart
helm dependency update k8s/devops-python-app
helm lint k8s/devops-python-app
helm template devops-python-app k8s/devops-python-app
helm install --dry-run --debug devops-python-app-test k8s/devops-python-app

# Bonus second chart
helm dependency update k8s/devops-python-app-v2
helm lint k8s/devops-python-app-v2
helm template devops-python-app-v2 k8s/devops-python-app-v2
```

### 6.4 Install dev environment

```powershell
helm install myapp-dev k8s/devops-python-app -f k8s/devops-python-app/values-dev.yaml
helm list
kubectl get all -l app.kubernetes.io/instance=myapp-dev
kubectl get svc
```

### 6.5 Upgrade release to prod settings

```powershell
helm upgrade myapp-dev k8s/devops-python-app -f k8s/devops-python-app/values-prod.yaml
helm get values myapp-dev
kubectl get deploy,svc -l app.kubernetes.io/instance=myapp-dev
```

### 6.6 Verify hooks

```powershell
kubectl get jobs
kubectl describe job myapp-dev-devops-python-app-pre-install
kubectl describe job myapp-dev-devops-python-app-post-install
kubectl logs job/myapp-dev-devops-python-app-pre-install
kubectl logs job/myapp-dev-devops-python-app-post-install
```

Note: hook jobs may be auto-deleted after success due to deletion policy. If so, verify via event history and Helm release output.

### 6.7 Bonus verification (library chart + second app)

```powershell
helm install myapp-v2 k8s/devops-python-app-v2
helm list
kubectl get all -l app.kubernetes.io/instance=myapp-v2
```

## 7. Operations Guide

### 7.1 Install

```bash
helm install myapp-dev k8s/devops-python-app -f k8s/devops-python-app/values-dev.yaml
```

### 7.2 Upgrade

```bash
helm upgrade myapp-dev k8s/devops-python-app -f k8s/devops-python-app/values-prod.yaml
```

### 7.3 Rollback

```bash
helm history myapp-dev
helm rollback myapp-dev 1
```

### 7.4 Uninstall

```bash
helm uninstall myapp-dev
helm uninstall myapp-v2
```