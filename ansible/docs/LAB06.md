# Lab 6: Advanced Ansible & CI/CD - Submission

**Student**: Selivanov George  
**Date**: March 5, 2026  
**Lab Points**: 10/10 (Bonus not implemented in this submission)

---

## 1. Overview

This lab upgrades the Lab 5 Ansible implementation to production-style automation:

- Refactored `common` and `docker` roles with `block`/`rescue`/`always`
- Added comprehensive tag strategy for selective execution
- Migrated deployment from `docker run` style to Docker Compose v2 via reusable `web_app` role
- Implemented safe wipe logic with double-gating (`web_app_wipe` variable + `web_app_wipe` tag)
- Added GitHub Actions workflow for lint + deploy + verification
- Added status badge to repository README

### 1.1 Updated Ansible Architecture

```text
ansible/
├── group_vars/all.yml
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
└── roles/
    ├── common/
    ├── docker/
    └── web_app/               # new role for Docker Compose deployment
        ├── defaults/main.yml
        ├── meta/main.yml
        ├── tasks/main.yml
        ├── tasks/wipe.yml
        └── templates/docker-compose.yml.j2
```

---

## 2. Task 1 — Blocks & Tags (2 pts)

## 2.1 `common` Role Refactor

**File**: `roles/common/tasks/main.yml`

Implemented:

- `Common package management block`
  - Tag: `packages`
  - Includes apt cache update, package installation, timezone
  - `rescue`: runs `apt-get update --fix-missing` and retries apt cache update
  - `always`: writes completion log to `/tmp/ansible-common-packages.log`
- `Common user management block`
  - Tag: `users`
  - Ensures users from `common_users` exist
  - `always`: writes completion log to `/tmp/ansible-common-users.log`

Role-level tag strategy is applied in playbook:

- `common` role tagged `common` in `playbooks/provision.yml`

## 2.2 `docker` Role Refactor

**File**: `roles/docker/tasks/main.yml`

Implemented:

- `Docker installation block`
  - Tags: `docker_install`, `docker`
  - Handles key, repo, apt update, package install
  - `rescue`: waits 10 seconds and retries key/repo/update/install
  - `always`: ensures Docker service is enabled and started
- `Docker configuration block`
  - Tags: `docker_config`, `docker`
  - Adds user to docker group
  - Installs `python3-docker`

Role-level tag strategy in playbook:

- `docker` role tagged `docker` in `playbooks/provision.yml`

## 2.3 Tag Execution Examples

```bash
# Docker only
ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Package tasks only
ansible-playbook playbooks/provision.yml --tags "packages"

# Docker installation block only
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Inspect tags
ansible-playbook playbooks/provision.yml --list-tags
```

## 2.4 Research Answers (Task 1)

1. **What happens if rescue block also fails?**  
   The task is marked failed and play execution follows normal Ansible failure behavior (stop on host unless `ignore_errors`/`max_fail_percentage` strategy changes it).

2. **Can you have nested blocks?**  
   Yes. Blocks can be nested for more granular error handling and directive scoping.

3. **How do tags inherit to tasks within blocks?**  
   Tags applied at block level are inherited by all tasks inside that block (including `rescue` and `always` tasks unless overridden).

## 3. Task 2 — Upgrade to Docker Compose (3 pts)

## 3.1 Role Rename and Migration

`app_deploy` usage was replaced by a new role named `web_app`.

**Playbook changes**:

- `playbooks/deploy.yml` now uses role `web_app` with role tags `web_app` and `app_deploy`

## 3.2 Docker Compose Template

**File**: `roles/web_app/templates/docker-compose.yml.j2`

Template supports:

- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `app_env_vars`
- `app_restart_policy`
- network declaration

## 3.3 Role Dependencies

**File**: `roles/web_app/meta/main.yml`

Dependency defined:

```yaml
dependencies:
  - role: docker
```

Result: running deploy playbook with `web_app` automatically ensures Docker role is executed first.

## 3.4 Compose Deployment Tasks

**File**: `roles/web_app/tasks/main.yml`

Implemented flow:

1. Include wipe logic (tag-isolated)
2. Create compose project directory (`/opt/{{ app_name }}` by default)
3. Template `docker-compose.yml`
4. Optional Docker Hub login (when creds provided)
5. Deploy via `community.docker.docker_compose_v2`
6. Wait for port
7. Verify `/health` endpoint

Tags:

- `app_deploy`
- `compose`

## 3.5 Variables Configuration

**File**: `group_vars/all.yml`

Configured variables:

- `app_name`, `docker_image`, `docker_tag`
- `app_port`, `app_internal_port`, `app_health_endpoint`
- `compose_project_dir`, `docker_compose_version`
- `app_env_vars`
- `web_app_wipe`
- Docker Hub credentials

> Security note: This file should be encrypted with Ansible Vault before production use.

## 3.6 Research Answers (Task 2)

1. **Difference between `restart: always` and `restart: unless-stopped`?**  
   `always` restarts even if container was manually stopped after daemon restart; `unless-stopped` restarts automatically except containers manually stopped by operator.

2. **How do Docker Compose networks differ from default Docker bridge networks?**  
   Compose creates project-scoped user-defined networks with built-in service DNS and better isolation; default bridge is global and less structured for multi-service apps.

3. **Can Ansible Vault variables be referenced in templates?**  
   Yes. Vault-encrypted vars are decrypted at runtime and can be used like normal variables in Jinja2 templates.

---

## 4. Task 3 — Wipe Logic (1 pt)

## 4.1 Implementation

**Files**:

- `roles/web_app/defaults/main.yml`
- `roles/web_app/tasks/wipe.yml`
- `roles/web_app/tasks/main.yml`

Safety model implemented exactly as required:

- Variable gate: `web_app_wipe: false` by default
- Tag gate: wipe tasks tagged `web_app_wipe`
- Wipe include placed at top of `main.yml` to support clean reinstall flow

Wipe tasks include:

- Compose down (`state: absent`)
- Remove `docker-compose.yml`
- Remove app directory
- Log completion message

## 4.2 Wipe Test Scenarios

```bash
# Scenario 1: normal deployment (wipe should not run)
ansible-playbook playbooks/deploy.yml

# Scenario 2: wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

# Scenario 3: clean reinstall (wipe -> deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# Scenario 4a: tag but variable false (wipe blocked)
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

## 4.3 Research Answers (Task 3)

1. **Why use both variable and tag?**  
   Double-safety: accidental tag-only or variable-only runs cannot wipe resources unintentionally.

2. **Difference from `never` tag?**  
   `never` blocks execution unless explicitly tagged but does not add variable-level intent confirmation. Variable+tag provides two independent approvals.

3. **Why wipe before deployment in `main.yml`?**  
   Supports clean reinstall lifecycle in one run: remove stale state first, then deploy fresh resources.

4. **When clean reinstall vs rolling update?**  
   Clean reinstall is better for drifted/broken environments; rolling update is preferred for minimizing downtime in stable production.

5. **How to extend wipe to images and volumes?**  
   Add optional gated tasks for `docker image rm` and `docker volume rm` (or Compose with `volumes: true` options) behind additional boolean variables.

---

## 5. Task 4 — CI/CD with GitHub Actions (3 pts)

## 5.1 Workflow Added

**File**: `.github/workflows/ansible-deploy.yml`

Workflow features:

- Trigger on push/PR for `ansible/**` and workflow file
- Excludes `ansible/docs/**` via path filter
- `lint` job:
  - installs Ansible + ansible-lint
  - installs `community.docker` + `community.general`
  - runs lint on playbooks
- `deploy` job (push only):
  - SSH setup
  - Vault password file injection from secret
  - runs `playbooks/deploy.yml`
  - verifies `/` and `/health` by curl

## 5.2 Required Manual Setup (Step-by-Step)

These steps require your GitHub account/repository settings.

1. Open repository settings:  
   `GitHub -> Settings -> Secrets and variables -> Actions`
2. Add required secrets with your values:
   - `ANSIBLE_VAULT_PASSWORD`
   - `SSH_PRIVATE_KEY`
   - `VM_HOST`
   - `VM_USER`
3. Ensure VM allows SSH from GitHub-hosted runner IP ranges (or use self-hosted runner).
4. Ensure Docker and Python are present on VM.
5. Push any change in `ansible/**` to trigger workflow.
6. Validate Actions logs and deployment endpoint checks.

## 5.3 Status Badge

Badge added to root `README.md`:

- `Ansible Deployment` workflow status badge

## 5.4 Research Answers (Task 4)

1. **Security implications of SSH keys in GitHub Secrets?**  
   Secrets are encrypted at rest, but exposure risk remains via workflow misuse, compromised maintainers, or logs. Mitigate with least-privilege keys, protected branches, and environment approvals.

2. **How to implement staging -> production pipeline?**  
   Use two jobs/environments: deploy to staging, run verification tests, require manual approval gate, then deploy to production with separate secrets and inventory.

3. **What to add for rollbacks?**  
   Versioned image tags, release metadata, previous-known-good compose file/tag retention, and a rollback workflow/job that redeploys prior tag automatically.

4. **How does self-hosted runner improve security vs GitHub-hosted?**  
   It keeps network and credentials inside your infrastructure boundary and can avoid exposing SSH ingress publicly, though it requires hardening and patch management.

---

## 6. Task 5 — Documentation (1 pt)

This file (`ansible/docs/LAB06.md`) documents:

- Implementation details for all required tasks
- Command-based test scenarios
- Safety mechanisms and rationale
- CI/CD architecture and operational setup
- Research analysis answers
