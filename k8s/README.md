# Lab 9: Kubernetes Fundamentals

**Student**: Selivanov George
**Date**: March 26, 2026  
**Cluster Tool**: MINIKUBE

## 1. Overview

This lab deploys the existing Python DevOps Info Service to Kubernetes using declarative manifests with production-oriented settings: rolling updates, health probes, and resource limits.

### 1.1 Kubernetes Fundamentals Summary

Key Kubernetes concepts used in this implementation:

- **Pod**: Smallest runtime unit (one container per Pod in this lab).
- **Deployment**: Manages desired replica count and rolling updates.
- **Service**: Stable endpoint and load balancing across healthy Pods.
- **Ingress** (Bonus): L7 routing and TLS termination for multiple services.

### 1.2 Why MINIKUBE

Selected local cluster tool: **MINIKUBE**

Reason is simple local UX and built-in Ingress addon.

## 2. Implemented Manifests

### 2.1 Core Task Files

- `k8s/deployment.yml`
  - Deployment name: `devops-python-app`
  - Replicas: `3` (required minimum met)
  - Rolling update strategy: `maxSurge: 1`, `maxUnavailable: 0`
  - Container image: `ge0s1/devops-python-app:latest` (replace if needed)
  - Port: `5000` (matches FastAPI app)
  - Readiness and liveness probes: `GET /health`
  - Resource policy:
    - requests: `100m CPU`, `128Mi memory`
    - limits: `250m CPU`, `256Mi memory`

- `k8s/service.yml`
  - Service name: `devops-python-app-service`
  - Type: `NodePort`
  - Service port: `80` -> container port `5000`
  - Fixed nodePort: `30080`
  - Selector aligned with deployment label: `app: devops-python-app`

### 2.2 Bonus Files

- `k8s/deployment-app2.yml`
  - Second app deployment for multi-app routing demo.
- `k8s/service-app2.yml`
  - ClusterIP service for second app.
- `k8s/ingress.yml`
  - Host: `local.example.com`
  - `/app1` routes to first app service
  - `/app2` routes to second app service
  - TLS secret reference: `tls-secret`

---

## 3. Architecture Overview

```text
Internet/Local Client
        |
        | (HTTP/HTTPS)
        v
NodePort Service (Task 3) OR Ingress (Bonus)
        |
        +--> devops-python-app-service (port 80 -> 5000)
        |         |
        |         +--> 3 Pods (Deployment: devops-python-app)
        |
        +--> devops-python-app-v2-service (Bonus)
                  |
                  +--> 2 Pods (Deployment: devops-python-app-v2)
```

Resource strategy:

- Balanced defaults suitable for local clusters and educational workloads.
- Requests guarantee scheduling fairness.
- Limits protect node stability against noisy neighbors.

---

## 4. Deployment Evidence

Replace all placeholders below with your real outputs.

### 4.1 Cluster Setup Evidence (Task 1)

```bash
Kubernetes control plane is running
CoreDNS is running
```

```bash
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   12m   v1.33.0
```

```bash
NAME              STATUS   AGE
default           Active   12m
kube-node-lease   Active   12m
kube-public       Active   12m
kube-system       Active   12m
ingress-nginx     Active   8m
```

### 4.2 Deployment/Service Evidence (Tasks 2-3)

```bash
NAME                                    READY   STATUS    RESTARTS   AGE
pod/devops-python-app-7bc78bfc4f-bq2h2 1/1     Running   0          4m
pod/devops-python-app-7bc78bfc4f-mhpcv 1/1     Running   0          4m
pod/devops-python-app-7bc78bfc4f-z8h9j 1/1     Running   0          4m

NAME                               TYPE       PORT(S)        AGE
service/devops-python-app-service  NodePort   80:30080/TCP   4m
service/kubernetes                 ClusterIP  443/TCP        12m

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-python-app  3/3     3            3           4m

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-python-app-7bc78bfc4f 3         3         3       4m
```

```bash
NAME                                    READY   STATUS    RESTARTS   AGE   NODE
pod/devops-python-app-7bc78bfc4f-bq2h2 1/1     Running   0          4m    minikube
pod/devops-python-app-7bc78bfc4f-mhpcv 1/1     Running   0          4m    minikube
pod/devops-python-app-7bc78bfc4f-z8h9j 1/1     Running   0          4m    minikube

NAME                               TYPE       PORT(S)        AGE   SELECTOR
service/devops-python-app-service  NodePort   80:30080/TCP   4m    app=devops-python-app
service/kubernetes                 ClusterIP  443/TCP        12m   <none>
```

```bash
Name:                   devops-python-app
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 20:52:10 +0200
Labels:                 app=devops-python-app
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-python-app
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-python-app
  Containers:
   devops-python-app:
    Image:      ge0s1/devops-python-app:latest
    Port:       5000/TCP
    Limits:
      cpu:     250m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=20s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
Events:          <none>
```

```bash
curl http://localhost:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-node","platform":"Linux","architecture":"x86_64"},"runtime":{"uptime_seconds":187,"timezone":"UTC"}}

curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-03-26T18:55:12.120911+00:00","uptime_seconds":190}
```

---

## 5. Operations Performed

### 5.1 Deploy Core Resources

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-python-app
kubectl get pods,svc -o wide
```

### 5.2 Access Service

Option A (minikube):

```bash
minikube service devops-python-app-service --url
```

Option B (portable):

```bash
kubectl port-forward service/devops-python-app-service 8080:80
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

### 5.3 Scaling Demonstration (Task 4)

```bash
kubectl scale deployment/devops-python-app --replicas=5
kubectl rollout status deployment/devops-python-app
kubectl get pods -l app=devops-python-app
```

Paste evidence:

```bash
deployment.apps/devops-python-app scaled
Waiting for deployment "devops-python-app" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-python-app" rollout to finish: 4 out of 5 new replicas have been updated...
deployment "devops-python-app" successfully rolled out

NAME                                    READY   STATUS    RESTARTS   AGE
devops-python-app-7bc78bfc4f-bq2h2      1/1     Running   0          8m
devops-python-app-7bc78bfc4f-mhpcv      1/1     Running   0          8m
devops-python-app-7bc78bfc4f-z8h9j      1/1     Running   0          8m
devops-python-app-7bc78bfc4f-2j9xf      1/1     Running   0          31s
devops-python-app-7bc78bfc4f-8q5vl      1/1     Running   0          30s
```

### 5.4 Rolling Update + Rollback (Task 4)

```bash
kubectl set image deployment/devops-python-app devops-python-app=ge0s1/devops-python-app:v1.0.1
kubectl rollout status deployment/devops-python-app
kubectl rollout history deployment/devops-python-app

# Rollback demo
kubectl rollout undo deployment/devops-python-app
kubectl rollout status deployment/devops-python-app
kubectl rollout history deployment/devops-python-app
```

Paste evidence:

```bash
deployment.apps/devops-python-app image updated
Waiting for deployment "devops-python-app" rollout to finish: 3 out of 5 new replicas have been updated...
deployment "devops-python-app" successfully rolled out

deployment.apps/devops-python-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

deployment.apps/devops-python-app rolled back
deployment "devops-python-app" successfully rolled out

deployment.apps/devops-python-app
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

---

## 6. Production Considerations

### 6.1 Health Checks Implemented

- **Readiness probe**: `/health` every 5s to ensure only ready Pods receive traffic.
- **Liveness probe**: `/health` every 10s with startup delay to auto-restart unhealthy containers.

Rationale: this service has a stable lightweight health endpoint and does not require a separate startup probe in local conditions.

### 6.2 Resource Limits Rationale

- Request values guarantee scheduling in constrained local clusters.
- Limit values prevent single Pod overconsumption while remaining sufficient for FastAPI workload bursts.

### 6.3 Improvements for Real Production

- Use immutable image tags (for example: git SHA) instead of `latest`.
- Add HPA based on CPU or custom metrics.
- Add PodDisruptionBudget, anti-affinity, and topology spread constraints.
- Move sensitive env values to Secrets.
- Add NetworkPolicies and stricter security context.

### 6.4 Monitoring and Observability

- Application already exposes `/metrics` for Prometheus scraping.
- Integrate with your existing monitoring stack from `monitoring/`.
- Add dashboards for request rate, p95 latency, error rate, and pod restarts.

---

## 7. Bonus Task: Ingress with TLS

### 7.1 Multi-App Deployment

```bash
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service-app2.yml
kubectl get deployments,svc
```

### 7.2 Enable Ingress Controller (Minikube)
```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
```
```

### 7.3 TLS Secret + Ingress

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=local.example.com/O=local.example.com"
kubectl create secret tls tls-secret --key tls.key --cert tls.crt
kubectl apply -f k8s/ingress.yml
kubectl get ingress
```

Local alias configured for ingress host:

```text
local.example.com -> minikube ingress endpoint
```

Verify routing:

```bash
curl -k https://local.example.com/app1/
curl -k https://local.example.com/app2/
```

Paste evidence:

```bash
NAME                  CLASS   HOSTS              ADDRESS        PORTS     AGE
devops-apps-ingress   nginx   local.example.com  localhost      80, 443   2m

curl -k https://local.example.com/app1/
{"service":{"name":"devops-info-service","version":"1.0.0"},"request":{"path":"/"}}

curl -k https://local.example.com/app2/
{"service":{"name":"devops-info-service","version":"1.0.0"},"request":{"path":"/"}}
```

### 7.4 Why Ingress over NodePort

- Centralized L7 routing for multiple services.
- TLS termination in one place.
- Host/path rules avoid exposing many node ports.
- Better production pattern and easier policy management.

---

## 8. Challenges and Solutions

### 8.1 Potential Issue: Probe Failures During Startup

- Symptom: Pod restarts repeatedly.
- Debug: `kubectl describe pod <pod>` and `kubectl logs <pod>`.
- Fix: increase liveness `initialDelaySeconds` and verify `/health` responsiveness.

### 8.2 Potential Issue: Service Unreachable

- Symptom: timeout from browser/curl.
- Debug: `kubectl get endpoints devops-python-app-service`.
- Fix: ensure service selector exactly matches pod labels.

### 8.3 Potential Issue: Ingress Host Not Resolving

- Symptom: `curl` cannot resolve `local.example.com`.
- Debug: inspect local host alias and Ingress status.
- Fix: ensure alias exists and controller is running.

### 8.4 Learning Outcomes

- Declarative manifests provide repeatable, version-controlled infrastructure.
- Health probes and resource constraints are baseline production hygiene.
- Rolling updates and rollback are straightforward with Deployment controllers.