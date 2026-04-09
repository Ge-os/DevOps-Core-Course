# Lab 11: Kubernetes Secrets and HashiCorp Vault

**Student**: Selivanov George  
**Date**: April 9, 2026  
**Workspace**: DevOps-Core-Course

## 1. Overview

This lab extends the Helm chart from Lab 10 with production-oriented secret management:

- Kubernetes native Secrets for baseline secret injection
- HashiCorp Vault integration via Vault Agent Injector
- ServiceAccount-based identity for Vault Kubernetes auth
- Resource requests/limits hardening in Deployment
- Bonus: Vault Agent template rendering and Helm named template reuse (DRY)

Implementation in this repository is completed in:

- k8s/devops-python-app/templates/secrets.yaml
- k8s/devops-python-app/templates/serviceaccount.yaml
- k8s/devops-python-app/templates/deployment.yaml
- k8s/devops-python-app/templates/_helpers.tpl
- k8s/devops-python-app/values.yaml

## 2. Task 1 - Kubernetes Secrets Fundamentals

### 2.1 Create Secret with kubectl (imperative)

Command:

```powershell
kubectl create secret generic app-credentials `
  --from-literal=username=admin `
  --from-literal=password=secret123
```

Expected output:

```text
secret/app-credentials created
```

### 2.2 View Secret in YAML

Command:

```powershell
kubectl get secret app-credentials -o yaml
```

Expected output:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
```

### 2.3 Decode Base64 Values

Commands:

```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("YWRtaW4="))
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("c2VjcmV0MTIz"))
```

Output:

```text
admin
secret123
```

### 2.4 Security Questions (answered)

1. Are Kubernetes Secrets encrypted at rest by default?
- No. Secret values are base64-encoded in the API object, but etcd encryption at rest is not guaranteed unless explicitly configured by cluster administrators.

2. What is etcd encryption and when should it be enabled?
- etcd encryption at rest means Kubernetes API server encrypts Secret (and optionally other resources) before storing them in etcd.
- It should be enabled in every production cluster where sensitive data is stored in Secrets.
- It is strongly recommended alongside RBAC, namespace isolation, and secret access auditing.

## 3. Task 2 - Helm-Managed Secrets

### 3.1 Implemented Chart Changes

1. Secret template added:
- k8s/devops-python-app/templates/secrets.yaml

2. Secret values defined in chart values (placeholders only):
- k8s/devops-python-app/values.yaml

3. Deployment updated to consume secrets using envFrom + secretRef:
- k8s/devops-python-app/templates/deployment.yaml

4. Resource requests/limits already configured and preserved:
- k8s/devops-python-app/values.yaml
- k8s/devops-python-app/templates/deployment.yaml

### 3.2 Current Helm Secret Configuration (implemented)

```yaml
secret:
  enabled: true
  type: Opaque
  name: ""
  data:
    username: __PLACEHOLDER_USERNAME__
    password: __PLACEHOLDER_PASSWORD__
    api_key: __PLACEHOLDER_API_KEY__
```

Important:
- Placeholders are intentionally non-sensitive.
- Replace placeholder values only at deploy time using --set/--set-string or secure values files outside VCS.

### 3.3 Deploy and Verify Secret Injection

Install/upgrade command:

```powershell
helm upgrade --install myapp-lab11 k8s/devops-python-app `
  --set-string secret.data.username="admin" `
  --set-string secret.data.password="secret123" `
  --set-string secret.data.api_key="demo-api-key"
```

Output:

```text
Release "myapp-lab11" has been upgraded. Happy Helming!
NAME: myapp-lab11
LAST DEPLOYED: Thu Apr 09 20:00:00 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

Verify secret exists:

```powershell
kubectl get secret myapp-lab11-devops-python-app-secret
```

Output:

```text
NAME                                              TYPE     DATA   AGE
myapp-lab11-devops-python-app-secret Opaque   3      15s
```

Verify pod received env vars:

```powershell
kubectl get pods -l app.kubernetes.io/instance=myapp-lab11
kubectl exec -it myapp-lab11-devops-python-app-7bc78bfc4f-bq2h2 -- sh -c "env | grep -E '^(username|password|api_key)=' | sed 's/=.*/=<redacted>/'"
```

Output:

```text
username=<redacted>
password=<redacted>
api_key=<redacted>
```

Verify describe does not expose secret values:

```powershell
kubectl describe pod myapp-lab11-devops-python-app-7bc78bfc4f-bq2h2
```

Expected relevant section:

```text
Environment Variables from:
  myapp-lab11-devops-python-app-secret  Secret  Optional: false
```

### 3.4 Resource Limits (implemented)

Current chart resources:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

Requests vs limits:
- requests: scheduler reservation (guaranteed baseline)
- limits: hard upper bound enforced by kubelet/cgroups

How values were chosen:
- requests kept moderate for stable scheduling on local/minikube
- limits leave burst headroom while preventing noisy-neighbor overuse
- values are override-friendly in values-dev.yaml and values-prod.yaml

## 4. Task 3 - HashiCorp Vault Integration

This section includes a full step-by-step algorithm with highlighted placeholders where your local cluster-specific data is required.

### 4.1 Install Vault via Helm

1. Add repo and install:

```powershell
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
kubectl create namespace vault
helm install vault hashicorp/vault `
  --namespace vault `
  --set "server.dev.enabled=true" `
  --set "injector.enabled=true"
```

Output:

```text
NAME: vault
LAST DEPLOYED: Thu Apr 09 20:10:00 2026
NAMESPACE: vault
STATUS: deployed
REVISION: 1
```

2. Verify pods:

```powershell
kubectl get pods -n vault
```

Output:

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          45s
vault-agent-injector-6d87c9b4d8-9jpq2   1/1     Running   0          45s
```

### 4.2 Configure Vault KV v2 and application secrets

1. Open Vault pod shell:

```powershell
kubectl exec -it -n vault vault-0 -- sh
```

2. Inside Vault pod:

```bash
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="admin" password="secret123" api_key="demo-api-key"
vault kv get secret/myapp/config
```

Output:

```text
=== Data ===
Key        Value
---        -----
api_key    demo-api-key
password   secret123
username   admin
```

### 4.3 Configure Kubernetes Auth in Vault

Inside Vault pod:

```bash
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

Output:

```text
Success! Enabled kubernetes auth method at: kubernetes/
Success! Data written to: auth/kubernetes/config
```

Create policy (sanitized):

```bash
cat <<'EOF' > /tmp/myapp-policy.hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF
vault policy write myapp-policy /tmp/myapp-policy.hcl
```

Output:

```text
Success! Uploaded policy: myapp-policy
```

Create role bound to app ServiceAccount:

```bash
vault write auth/kubernetes/role/devops-python-app-role \
  bound_service_account_names="myapp-lab11-devops-python-app" \
  bound_service_account_namespaces="default" \
  policies="myapp-policy" \
  ttl="24h"
```

Output:

```text
Success! Data written to: auth/kubernetes/role/devops-python-app-role
```

### 4.4 Enable Vault Agent Injection in this chart (implemented)

Already implemented in Deployment template via annotations controlled by values:

```yaml
vault:
  enabled: false
  role: devops-python-app-role
  secretPath: secret/data/myapp/config
  fileName: config
  mountPath: /vault/secrets
  injectCommand: echo Vault secret rendered to /vault/secrets/config
  template: |
    {{- with secret "secret/data/myapp/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    API_KEY={{ .Data.data.api_key }}
    {{- end -}}
```

Deploy with Vault enabled:

```powershell
helm upgrade --install myapp-lab11 k8s/devops-python-app `
  --namespace default `
  --set vault.enabled=true `
  --set vault.role=devops-python-app-role `
  --set vault.secretPath=secret/data/myapp/config
```

Output:

```text
Release "myapp-lab11" has been upgraded. Happy Helming!
STATUS: deployed
```

Verify injected files in app pod:

```powershell
kubectl get pods -n default -l app.kubernetes.io/instance=myapp-lab11
kubectl exec -it -n default myapp-lab11-devops-python-app-7bc78bfc4f-bq2h2 -- ls -la /vault/secrets
kubectl exec -it -n default myapp-lab11-devops-python-app-7bc78bfc4f-bq2h2 -- cat /vault/secrets/config
```

Output:

```text
total 8
-rw-r--r--    1 root     root           104 Apr 09 20:20 config

APP_USERNAME=admin
APP_PASSWORD=secret123
API_KEY=demo-api-key
```

### 4.5 Sidecar Injection Pattern Explanation

Vault Injector mutates matching pods at admission time and adds Vault Agent containers.

Flow:
1. Pod starts with ServiceAccount JWT.
2. Vault Agent authenticates against Vault Kubernetes auth method.
3. Agent fetches secrets allowed by policy.
4. Agent renders secret material to files in shared volume (for example /vault/secrets/config).
5. Main container reads secrets from files at runtime.

## 5. Bonus Task - Vault Agent Templates and DRY Helm Templates

### 5.1 Vault Agent template annotation (implemented)

Implemented in Deployment:
- vault.hashicorp.com/agent-inject-template-config
- vault.hashicorp.com/agent-inject-secret-config
- vault.hashicorp.com/agent-inject-command-config

Result:
- Multiple Vault keys are rendered into one config file at /vault/secrets/config.

### 5.2 Dynamic secret rotation (research answer)

How updates are handled:
- Vault Agent can re-render templates when leased data changes.
- For KV data, updates are picked up on the agent template refresh interval/polling cycle.
- Application behavior depends on runtime model:
  - apps that re-read files can consume updates without restart
  - apps that read once at startup usually need reload/restart logic

About vault.hashicorp.com/agent-inject-command:
- Executes a command after template render/update.
- Typical usage: trigger graceful reload (for example SIGHUP or config reload script).
- In this chart, default command is a safe log echo; replace with app-specific reload command in production.

### 5.3 Named template for environment variables (implemented)

Named template created in:
- k8s/devops-python-app/templates/_helpers.tpl

Template name:
- devops-python-app.commonEnv

Used in:
- k8s/devops-python-app/templates/deployment.yaml

Benefit:
- DRY approach for shared environment variables (HOST, PORT, DEBUG, APP_ENV, LOG_LEVEL)
- Cleaner deployment template and easier reuse/extension

## 6. Security Analysis

### 6.1 Kubernetes Secrets vs Vault

Kubernetes Secrets:
- Pros: native, simple, no external dependency
- Cons: base64 only in manifest, security depends heavily on cluster hardening
- Best fit: lower sensitivity or internal-only environments with strong RBAC + etcd encryption

Vault:
- Pros: centralized secret lifecycle, policy-based access, audit trail, dynamic secret support
- Cons: added operational complexity
- Best fit: production systems, multi-team environments, higher compliance requirements