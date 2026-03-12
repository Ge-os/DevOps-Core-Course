# Monitoring Ansible Role

This Ansible role deploys the Grafana Loki monitoring stack including Loki 3.0, Promtail 3.0, and Grafana 11.3.1.

## Requirements

- Ansible 2.16+
- Docker Engine 20.10+
- Docker Compose v2
- Python 3.8+
- `community.docker` Ansible collection

## Role Variables

See `defaults/main.yml` for all available variables. Key variables:

```yaml
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

# Grafana security
grafana_admin_user: "admin"
grafana_admin_password: "{{ vault_grafana_password }}"
grafana_anonymous_enabled: false

# Application integration
python_app_enabled: true
python_app_port: 8000
```

## Dependencies

- `docker` role (optional, if Docker needs to be installed)

## Example Playbook

```yaml
- hosts: monitoring_servers
  become: true
  roles:
    - role: monitoring
      vars:
        loki_retention_period: "168h"
        grafana_anonymous_enabled: false
```

## Usage

### Deploy Monitoring Stack

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml
```

### Test Idempotency

```bash
# Run twice and verify second run shows 0 changes
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml
```

### Deploy with Custom Variables

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml \
  -e "loki_retention_period=336h" \
  -e "grafana_port=3001"
```

### Deploy Only Setup Tasks

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --tags setup
```

### Deploy Only to Specific Hosts

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --limit monitoring-server-01
```

## Features

- **Automated Deployment**: Complete stack deployment with one command
- **Idempotent**: Safe to run multiple times
- **Templated Configs**: Easy to customize via variables
- **Health Checks**: Automatic service health verification
- **Grafana Provisioning**: Auto-configured Loki datasource
- **Security**: Secrets managed via Ansible Vault
- **Resource Limits**: Configurable resource constraints
- **Multi-Environment**: Support for dev/staging/prod

## Architecture

The role deploys:

1. **Loki**: Log aggregation with TSDB storage
2. **Promtail**: Docker log collector with service discovery
3. **Grafana**: Visualization with pre-configured Loki datasource
4. **Python App** (optional): Application with JSON logging

All services run in Docker containers managed by Docker Compose.

## File Structure

```
monitoring/
├── defaults/main.yml       # Default variables
├── tasks/
│   ├── main.yml           # Main orchestration
│   ├── setup.yml          # Directory and config setup
│   └── deploy.yml         # Docker Compose deployment
├── templates/
│   ├── docker-compose.yml.j2  # Docker Compose template
│   ├── loki-config.yml.j2     # Loki configuration
│   ├── promtail-config.yml.j2 # Promtail configuration
│   └── env.j2                 # Environment variables
├── handlers/main.yml      # Service restart handlers
└── meta/main.yml          # Role metadata
```

## Post-Deployment

After deployment, the stack is available at:

- **Grafana**: http://localhost:3000
- **Loki API**: http://localhost:3100
- **Promtail**: http://localhost:9080

Default credentials:
- Username: `admin`
- Password: (from vault or default)

## Security Considerations

1. **Change Default Password**: Use Ansible Vault for `grafana_admin_password`
2. **Disable Anonymous Access**: Set `grafana_anonymous_enabled: false`
3. **Secure Docker Socket**: Promtail has read-only access
4. **Network Isolation**: Services run on isolated Docker network
5. **Resource Limits**: Prevents resource exhaustion

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker compose -f /opt/monitoring/docker-compose.yml logs

# Check service status
docker compose -f /opt/monitoring/docker-compose.yml ps
```

### Promtail Not Finding Containers

Ensure containers have the label:
```yaml
labels:
  logging: "promtail"
```

### Loki Out of Memory

Increase memory limits in variables:
```yaml
loki_memory_limit: "2G"
```

### Grafana Can't Connect to Loki

Check network connectivity:
```bash
docker exec grafana curl http://loki:3100/ready
```

## Testing

Test the role:

```bash
# Syntax check
ansible-playbook playbooks/deploy-monitoring.yml --syntax-check

# Dry run
ansible-playbook playbooks/deploy-monitoring.yml --check

# Full deployment
ansible-playbook playbooks/deploy-monitoring.yml

# Idempotency test
ansible-playbook playbooks/deploy-monitoring.yml
# Should show 0 changed
```

## License

MIT

## Author

Selivanov George (Lab 7, DevOps Core Course)
