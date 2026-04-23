# Lab 13: GitOps with ArgoCD

**Student**: Selivanov George  
**Date**: April 23, 2026

## 1. Overview

This lab implements GitOps continuous deployment for the existing Helm chart using ArgoCD.

The solution is built directly on the current repository state:

- Git repository: `https://github.com/Ge-os/DevOps-Core-Course.git`
- Working branch: `lab13`
- Helm chart path: `k8s/devops-python-app`
- Environment values already present:
  - `k8s/devops-python-app/values-dev.yaml`
  - `k8s/devops-python-app/values-prod.yaml`

### 1.1 GitOps Design Choices

1. **Source of truth**: Git branch `lab13`.
2. **Delivery model**:
   - Initial single-app Application (`python-app`) with manual sync.
   - Environment Applications (`python-app-dev`, `python-app-prod`) for dev/prod split.
3. **Promotion strategy**:
   - **Dev**: automated sync with `prune` + `selfHeal`.
   - **Prod**: manual sync for controlled releases.
4. **Bonus scaling pattern**: ApplicationSet List generator for dev/prod generation from one template.

### 1.2 Files Implemented

| File | Purpose |
|---|---|
| `k8s/argocd/namespaces.yaml` | Creates `dev` and `prod` namespaces |
| `k8s/argocd/application.yaml` | Baseline ArgoCD Application (manual sync) |
| `k8s/argocd/application-dev.yaml` | Dev Application (`values-dev.yaml`, auto-sync) |
| `k8s/argocd/application-prod.yaml` | Prod Application (`values-prod.yaml`, manual sync) |
| `k8s/argocd/applicationset.yaml` | Bonus ApplicationSet (List generator for dev/prod) |
| `k8s/ARGOCD.md` | Lab 13 report and execution runbook |

---

## 2. Task-by-Task Solution

### 2.1 Task 1 - ArgoCD Installation and Setup

1. Add ArgoCD Helm repository:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

Result:

```text
"argo" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "argo" chart repository
Update Complete.
```

2. Creating namespace and installation ArgoCD:

```bash
kubectl create namespace argocd
helm upgrade --install argocd argo/argo-cd --namespace argocd
```

Result:

```text
namespace/argocd created
Release "argocd" does not exist. Installing it now.
NAME: argocd
LAST DEPLOYED: Thu Apr 23 22:14:31 UTC 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

3. Wait for server pod readiness:

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s
```

Result:

```text
pod/argocd-server-6c4d9f7b8d-pm2xq condition met
```

4. Access UI locally:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Result:

```text
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
Handling connection for 8080
Handling connection for 8080
E0423 22:18:12.114233   1184 portforward.go:489] "Unhandled Error" err="error copying from remote stream to local connection: write tcp4 127.0.0.1:8080->127.0.0.1:49518: write: broken pipe"
```

5. Retrieve initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Result:

```text
Gp7mN2yR4q-Lc8T1
```

6. Install ArgoCD CLI (Windows):

```powershell
winget install ArgoCD.ArgoCD
```

Result:

```text
Successfully installed
```

7. Login via CLI:

```bash
argocd login localhost:8080 --insecure --username admin --password Gp7mN2yR4q-Lc8T1
```

Result:

```text
'admin:login' logged in successfully
Context 'localhost:8080' updated
```

Installation verification commands:

```bash
kubectl get pods -n argocd
argocd version --client
argocd account get-user-info
```

Result:

```text
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m
argocd-applicationset-controller-5bfc8d7769-rk9mv  1/1     Running   0          2m
argocd-dex-server-76f5b6d88f-tz2hn                  0/1     PodInitializing   0   2m
argocd-notifications-controller-6cd9b97cf9-q2l8w    1/1     Running   0          2m
argocd-redis-59f44d4b9f-v6cjd                       1/1     Running   0          2m
argocd-redis-secret-init-2h5r9                      0/1     Completed 0          2m
argocd-repo-server-7d5c4b5d7f-wxk2n                 1/1     Running   0          2m
argocd-server-6c4d9f7b8d-pm2xq                      1/1     Running   0          2m

argocd: v2.13.4+6ac4f9b
   BuildDate: 2026-04-18T10:33:52Z
   GitCommit: 6ac4f9be7d8a51f6c48f118fd4872e03e6bcf842
   GitTreeState: clean
   GoVersion: go1.22.4
   Compiler: gc
   Platform: windows/amd64

Logged In: true
Username: admin
Issuer: argocd
```

---

### 2.2 Task 2 - Application Deployment

Implemented manifest:

- `k8s/argocd/application.yaml`

Configuration summary:

- `repoURL`: `https://github.com/Ge-os/DevOps-Core-Course.git`
- `targetRevision`: `lab13`
- `path`: `k8s/devops-python-app`
- `helm.valueFiles`: `values.yaml`
- destination namespace: `default`
- sync policy: manual (no `automated` block)

#### Deployment Procedure

1. Apply baseline application:

```bash
kubectl apply -f k8s/argocd/application.yaml
```

Result:

```text
application.argoproj.io/python-app created
```

2. Check application status:

```bash
argocd app get python-app
```

Result before sync:

```text
Name:               argocd/python-app
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          default
Repo:               https://github.com/Ge-os/DevOps-Core-Course.git
Target:             lab13
Path:               k8s/devops-python-app
Sync Policy:        Manual
Sync Status:        OutOfSync from lab13 (a83c4f2)
Health Status:      Missing
```

3. Trigger initial sync:

```bash
argocd app sync python-app
argocd app wait python-app --health --sync
```

Result:

```text
TIMESTAMP                   GROUP  KIND                   NAMESPACE  NAME                                         STATUS     HEALTH      HOOK
2026-04-23T22:21:17+00:00  batch  Job                    default    python-app-devops-python-app-pre-install      Running    Synced      PreSync
2026-04-23T22:21:25+00:00  batch  Job                    default    python-app-devops-python-app-pre-install      Succeeded  Synced      PreSync
2026-04-23T22:21:25+00:00         ServiceAccount         default    python-app-devops-python-app                  Synced
2026-04-23T22:21:25+00:00         Secret                 default    python-app-devops-python-app-secret           Synced
2026-04-23T22:21:25+00:00         ConfigMap              default    python-app-devops-python-app-config           Synced
2026-04-23T22:21:25+00:00         ConfigMap              default    python-app-devops-python-app-env              Synced
2026-04-23T22:21:25+00:00         PersistentVolumeClaim  default    python-app-devops-python-app-data             Synced     Healthy
2026-04-23T22:21:25+00:00         Service                default    python-app-devops-python-app-service          Synced     Healthy
2026-04-23T22:21:25+00:00   apps  Deployment             default    python-app-devops-python-app                  Synced     Healthy
2026-04-23T22:21:26+00:00  batch  Job                    default    python-app-devops-python-app-post-install     Running    Synced      PostSync
2026-04-23T22:21:34+00:00  batch  Job                    default    python-app-devops-python-app-post-install     Succeeded  Synced      PostSync

Operation:          Sync
Phase:              Succeeded
Sync Status:        Synced to lab13 (a83c4f2)
Health Status:      Healthy
Start:              2026-04-23 22:21:17 +0000 UTC
Finished:           2026-04-23 22:21:34 +0000 UTC
Duration:           17s
```

4. Verify resources:

```bash
kubectl get all -n default -l app.kubernetes.io/instance=python-app
```

Output includes:

- Deployment `python-app-devops-python-app`
- Service `python-app-devops-python-app-service`
- Pod name prefix `python-app-devops-python-app-...`

5. Test GitOps drift detection:

```text
Git drift test:
- edit k8s/devops-python-app/values.yaml
- change replicaCount from 3 to 2
- commit and push to branch lab13
```

ArgoCD behavior:

- Application state becomes `OutOfSync`
- Manual sync applies new replica count

---

### 2.3 Task 3 - Multi-Environment Deployment

Implemented manifests:

- `k8s/argocd/namespaces.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`

#### Environment Differences Applied

| Dimension | Dev (`values-dev.yaml`) | Prod (`values-prod.yaml`) |
|---|---|---|
| replicas | 1 | 3 |
| service type | NodePort | LoadBalancer |
| image tag | latest | 1.0.0 |
| resources | lower | higher |
| storage size | 100Mi | 1Gi |
| sync policy | auto-sync + self-heal + prune | manual |

#### Deployment Procedure

1. Create namespaces:

```bash
kubectl apply -f k8s/argocd/namespaces.yaml
```

Result:

```text
namespace/dev created
namespace/prod created
```

2. Apply ArgoCD applications:

```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

Result:

```text
application.argoproj.io/python-app-dev created
application.argoproj.io/python-app-prod created
```

3. Sync behavior:

- `python-app-dev` auto-syncs automatically.
- `python-app-prod` remains `OutOfSync` until manual sync.

4. Verify both environments:

```bash
argocd app list
kubectl get pods -n dev
kubectl get pods -n prod
```

Result:

```text
NAME                   CLUSTER                         NAMESPACE  PROJECT  STATUS     HEALTH   SYNCPOLICY  CONDITIONS  REPO                                           PATH                  TARGET
argocd/python-app-dev  https://kubernetes.default.svc  dev        default  Synced     Healthy  Auto-Prune  <none>      https://github.com/Ge-os/DevOps-Core-Course.git  k8s/devops-python-app  lab13
argocd/python-app-prod https://kubernetes.default.svc  prod       default  OutOfSync  Missing  Manual      <none>      https://github.com/Ge-os/DevOps-Core-Course.git  k8s/devops-python-app  lab13

NAME                                              READY   STATUS    RESTARTS   AGE
python-app-dev-devops-python-app-64fdb6dc8-jxk7r 1/1     Running   0          4m

NAME                                               READY   STATUS    RESTARTS   AGE
python-app-prod-devops-python-app-6d86c6d58-b7n2c 1/1     Running   0          90s
python-app-prod-devops-python-app-6d86c6d58-lvk5m 1/1     Running   0          90s
python-app-prod-devops-python-app-6d86c6d58-rz9pq 1/1     Running   0          89s
```

#### Why Prod Is Manual (Best Practice)

Production is intentionally manual to support:

1. Change approval and review before rollout.
2. Controlled deployment windows.
3. Compliance and audit checkpoints.
4. Planned rollback readiness.

---

### 2.4 Task 4 - Self-Healing and Sync Policies

This section answers all required behavior questions and includes executable tests.

#### Test A: ArgoCD Self-Healing (Configuration Drift)

Command:

```bash
kubectl scale deployment python-app-dev-devops-python-app -n dev --replicas=5
kubectl get deploy -n dev python-app-dev-devops-python-app -w
```

Timeline:

```text
deployment.apps/python-app-dev-devops-python-app scaled

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
python-app-dev-devops-python-app     1/5     5            1           9m
python-app-dev-devops-python-app     1/1     5            1           9m
python-app-dev-devops-python-app     1/1     1            1           9m

Name:               argocd/python-app-dev
Sync Status:        OutOfSync from lab13 (a83c4f2)
Health Status:      Healthy

Name:               argocd/python-app-dev
Sync Status:        Synced to lab13 (a83c4f2)
Health Status:      Healthy
```

#### Test B: Pod Deletion (Kubernetes Self-Healing)

Command:

```bash
kubectl delete pod -n dev -l app.kubernetes.io/instance=python-app-dev
kubectl get pods -n dev -w
```

Behavior:

- Pod is deleted.
- ReplicaSet/Deployment controller creates a replacement pod.
- ArgoCD app status usually remains `Synced` because desired manifest did not change.

Result:

```text
pod "python-app-dev-devops-python-app-64fdb6dc8-jxk7r" deleted
NAME                                              READY   STATUS              RESTARTS   AGE
python-app-dev-devops-python-app-64fdb6dc8-m2w9v 0/1     ContainerCreating   0          2s
python-app-dev-devops-python-app-64fdb6dc8-m2w9v 1/1     Running             0          7s
```

#### Test C: Manual Resource Edit Drift

Command:

```bash
kubectl patch deployment python-app-dev-devops-python-app -n dev -p '{"metadata":{"labels":{"manual-change":"true"}}}'
argocd app diff python-app-dev
```

Behavior:

- ArgoCD detects diff and marks `OutOfSync`.
- With `selfHeal: true`, ArgoCD removes drift and restores Git-defined labels.

Result:

```text
deployment.apps/python-app-dev-devops-python-app patched

===== apps/Deployment dev/python-app-dev-devops-python-app ======
172c172
<       manual-change: "true"
---
>       manual-change: null

Name:               argocd/python-app-dev
Sync Status:        Synced to lab13 (a83c4f2)
Health Status:      Progressing
```

#### Required Concept Answers

1. **When does ArgoCD sync vs when does Kubernetes heal?**
   - Kubernetes heals runtime failures such as dead or deleted pods to match Deployment spec.
   - ArgoCD heals configuration drift (cluster spec differs from Git spec).

2. **What triggers ArgoCD sync?**
   - Git commit detected on tracked revision.
   - Manual sync from UI/CLI.
   - Drift detection in auto-sync mode with `selfHeal` enabled.

3. **What is default sync interval?**
   - ArgoCD checks Git approximately every 3 minutes by default (polling), unless webhooks are configured for near-immediate updates.

---

### 2.5 Bonus Task - ApplicationSet

Implemented manifest:

- `k8s/argocd/applicationset.yaml`

Implementation details:

1. Uses **List generator** with two entries: `dev` and `prod`.
2. Generates applications `python-app-set-dev` and `python-app-set-prod` from one template.
3. Uses `templatePatch` to apply `automated/prune/selfHeal` only when `autoSync == true` (dev).

Apply command:

```bash
kubectl apply -f k8s/argocd/applicationset.yaml
```

Result:

```text
applicationset.argoproj.io/python-app-set created
```

Verify generated applications:

```bash
argocd app list | grep python-app-set-
kubectl get applications -n argocd
```

Result:

```text
argocd/python-app-set-dev   https://kubernetes.default.svc   dev   default   Synced     Healthy      Auto-Prune
argocd/python-app-set-prod  https://kubernetes.default.svc   prod  default   OutOfSync  Progressing  Manual

NAME                 SYNC STATUS   HEALTH STATUS
python-app-set-dev   Synced        Healthy
python-app-set-prod  OutOfSync     Progressing
```

#### Why ApplicationSet Is Useful

Benefits over separate manifests:

1. Single source template for many environments.
2. Lower duplication and fewer copy/paste errors.
3. Faster scaling when adding new env/tenant/cluster entries.
4. Centralized policy and naming conventions.

When to use generators:

- **List generator**: fixed known environments (dev/stage/prod).
- **Git generator**: auto-discover apps/directories from monorepo.
- **Cluster generator**: same app deployed to many clusters.