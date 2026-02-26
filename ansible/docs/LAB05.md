# Lab 5: Ansible Fundamentals

**Student**: Selivanov George  
**Date**: February 26, 2026

---

## 1. Architecture Overview

**Ansible Version**: 2.16+  
**Target VM OS**: Ubuntu 24.04 LTS  
**Control Node**: Local machine (WSL2 / Linux)

### Role Structure

```
ansible/
├── inventory/hosts.ini         # Static inventory (localhost)
├── ansible.cfg                 # Global configuration
├── group_vars/all.yml          # Vault-encrypted variables
├── playbooks/
│   ├── site.yml                # Entry point (imports all)
│   ├── provision.yml           # Runs common + docker roles
│   └── deploy.yml              # Runs app_deploy role
└── roles/
    ├── common/                 # OS baseline packages & timezone
    ├── docker/                 # Docker CE installation + service
    └── app_deploy/             # Docker Hub pull + container run
```

**Why roles instead of monolithic playbooks?** Each role is self-contained and reusable — `docker` can be dropped into any project without changes.

---

## 2. Roles Documentation

### 2.1 `common`

**Purpose**: Baseline system setup — update apt cache, install essential tools, set timezone.

| Variable | Default | Description |
|----------|---------|-------------|
| `common_packages` | `[python3-pip, curl, git, vim, htop, ...]` | Packages to install |
| `common_timezone` | `UTC` | System timezone |

**Handlers**: None (apt installs are idempotent by design).  
**Dependencies**: None.

### 2.2 `docker`

**Purpose**: Install Docker CE from official repository, ensure service is running, add user to `docker` group.

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_packages` | `[docker-ce, docker-ce-cli, containerd.io, ...]` | Docker packages |
| `docker_user` | `{{ ansible_user }}` | User added to docker group |

**Handlers**: `restart docker` — triggered when Docker packages are (re)installed.  
**Dependencies**: `common` (apt cache must be fresh, `ca-certificates` installed).

### 2.3 `app_deploy`

**Purpose**: Login to Docker Hub, pull image, replace running container, verify health endpoint.

| Variable | Default | Description |
|----------|---------|-------------|
| `app_port` | `5000` | Host port mapped to container |
| `app_restart_policy` | `unless-stopped` | Container restart policy |
| `app_env_vars` | `{}` | Extra environment variables |
| `dockerhub_username` | *(vault)* | Docker Hub login |
| `dockerhub_password` | *(vault)* | Docker Hub token |
| `docker_image` | *(vault)* | Full image name |
| `docker_image_tag` | `latest` | Image tag |
| `app_container_name` | *(vault)* | Container name |

**Handlers**: `restart app` — triggered when container config changes.  
**Dependencies**: `docker` role must be applied first.

---

## 3. Idempotency Demonstration

### First Run (`provision.yml`)

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] **********************************************
changed: [devops-vm]

TASK [common : Install common packages] ***************************************
changed: [devops-vm]

TASK [common : Set system timezone] *******************************************
changed: [devops-vm]

TASK [docker : Add Docker GPG key] ********************************************
changed: [devops-vm]

TASK [docker : Add Docker repository] *****************************************
changed: [devops-vm]

TASK [docker : Update apt cache after adding Docker repo] *********************
changed: [devops-vm]

TASK [docker : Install Docker packages] ***************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************
changed: [devops-vm]

TASK [docker : Add user to docker group] **************************************
changed: [devops-vm]

TASK [docker : Install python3-docker] ****************************************
changed: [devops-vm]

RUNNING HANDLERS [docker : restart docker] ************************************
changed: [devops-vm]

PLAY RECAP ********************************************************************
devops-vm : ok=12  changed=10  unreachable=0  failed=0
```

**First run**: 10 tasks changed — all packages installed from scratch, Docker service started, handler fired once to restart Docker after package installation.

### Second Run (`provision.yml`)

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] **********************************************
ok: [devops-vm]

TASK [common : Install common packages] ***************************************
ok: [devops-vm]

TASK [common : Set system timezone] *******************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ********************************************
ok: [devops-vm]

TASK [docker : Add Docker repository] *****************************************
ok: [devops-vm]

TASK [docker : Update apt cache after adding Docker repo] *********************
ok: [devops-vm]

TASK [docker : Install Docker packages] ***************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************
ok: [devops-vm]

TASK [docker : Add user to docker group] **************************************
ok: [devops-vm]

TASK [docker : Install python3-docker] ****************************************
ok: [devops-vm]

PLAY RECAP ********************************************************************
devops-vm : ok=11  changed=0  unreachable=0  failed=0
```

**Second run**: 0 changes. Every task found the system already in desired state — packages installed (`state: present`), service running (`state: started`), user in group (`append: yes`). Handler not triggered because no packages changed.

**What makes roles idempotent**:
- `apt: state=present` — skips if already installed
- `service: state=started, enabled=yes` — skips if already running
- `user: groups=docker, append=yes` — skips if already member
- `apt_key` / `apt_repository` — check-before-add semantics

---

## 4. Ansible Vault Usage

All secrets live in `group_vars/all.yml`, encrypted with AES-256.

### Creating the vault file

```bash
cd ansible/
ansible-vault create group_vars/all.yml
# Enter vault password when prompted
```

### Contents (before encryption)

```yaml
dockerhub_username: ge0s1
dockerhub_password: <access-token>
app_name: devops-app
docker_image: "ge0s1/devops-python-app"
docker_image_tag: latest
app_port: 5000
app_container_name: devops-app
```

### Encrypted file (as committed to git)

```
$ANSIBLE_VAULT;1.1;AES256
66386439653761306566323263643639666665653862343066636130653331653331646665363930
3163363737303264323735396265373438386565396565350a306431363565623965393164303532
...
```

### Vault password management

```bash
# Store vault password locally (never commit!)
echo "123456" > .vault_pass
chmod 600 .vault_pass
```

`ansible.cfg` is configured to load it automatically:
```ini
vault_password_file = .vault_pass
```

`.vault_pass` is in `.gitignore`. The encrypted `group_vars/all.yml` is safe to commit.

**Why Ansible Vault?**  
Credentials in plaintext files get accidentally committed. Vault encrypts at rest, integrates transparently with playbooks, and leaves no secrets in logs (`no_log: true` on login tasks).

---

## 5. Deployment Verification

### Deploy run (`deploy.yml`)

```bash
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] *****************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] **************************************
ok: [devops-vm]

TASK [app_deploy : Pull Docker image] *****************************************
changed: [devops-vm]

TASK [app_deploy : Stop existing container if running] ************************
ok: [devops-vm]

TASK [app_deploy : Remove old container if exists] ****************************
ok: [devops-vm]

TASK [app_deploy : Run application container] *********************************
changed: [devops-vm]

TASK [app_deploy : Wait for application port to be available] *****************
ok: [devops-vm]

TASK [app_deploy : Verify application health endpoint] ************************
ok: [devops-vm]

PLAY RECAP ********************************************************************
devops-vm : ok=8   changed=2   unreachable=0   failed=0
```

### Container status

```bash
$ ansible webservers -a "docker ps"
devops-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                          COMMAND            CREATED          STATUS          PORTS                    NAMES
a3f9c2d1e4b7   ge0s1/devops-python-app:latest "python app.py"   12 seconds ago   Up 11 seconds   0.0.0.0:5000->5000/tcp   devops-app
```

### Health check

```bash
$ curl http://localhost:5000/health
{
  "status": "healthy",
  "timestamp": "2026-02-26T12:00:00+00:00",
  "uptime_seconds": 14
}

$ curl http://localhost:5000/
{
  "service": {"name": "DevOps Info Service", "version": "1.0.0"},
  "system": {"hostname": "devops-vm", ...},
  ...
}
```

**Handler execution**: `restart app` handler was NOT triggered on first deploy because the container was newly created (`state: started` with no existing container). On a second deploy where only the image tag changes, the handler triggers to restart the container with the new image.

---

## 6. Key Decisions

**Why roles instead of plain playbooks?**  
Each role (`common`, `docker`, `app_deploy`) can be used independently across different projects. A single task file would be 200+ lines with no structure — roles split responsibilities and make the code navigable.

**How do roles improve reusability?**  
The `docker` role has zero app-specific logic. Drop it into any playbook for any project and Docker gets installed identically. Variables in `defaults/main.yml` allow overriding without touching role code.

**What makes a task idempotent?**  
Using declarative Ansible modules (`apt: state=present`, `service: state=started`) instead of shell commands (`apt install`, `systemctl start`). Modules check current state before acting; `shell`/`command` always run.

**How do handlers improve efficiency?**  
The Docker `restart` handler fires once after all package tasks, not after each individual package install. Without handlers, Docker would restart 5 times during a multi-package install.

**Why is Ansible Vault necessary?**  
Credentials must exist somewhere to be usable. Without Vault, the only options are plaintext files (leak risk) or manual entry every time (no automation). Vault encrypts secrets at rest while keeping them in version control alongside the code that uses them.

---

## 7. Challenges

- **WSL2 on Windows**: Ansible only runs in Linux — used WSL2 Ubuntu as the control node. The `ansible.cfg` and inventory paths work in the WSL2 filesystem.
- **`community.docker` collection**: Not included in base Ansible — required `ansible-galaxy collection install community.docker` before running deploy playbook.
- **`apt_key` deprecation**: Ubuntu 22.04+ prefers `gpg`-based signed-by APT sources. Added `ca-certificates` to common packages first to avoid GPG errors.
