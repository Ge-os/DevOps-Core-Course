"""
Pulumi Infrastructure as Code for DevOps Lab 04
Cloud Provider: Yandex Cloud
Purpose: Provision a VM for Ansible configuration (Lab 05)
"""

import pulumi
import pulumi_yandex as yandex

# Configuration
config = pulumi.Config()

# Yandex Cloud Configuration
zone = config.get("yandex:zone") or "ru-central1-a"

# VM Configuration
vm_name = config.get("vmName") or "devops-lab04-vm-pulumi"
vm_user = config.get("vmUser") or "ubuntu"
ssh_public_key = config.require("sshPublicKey")

# VM Resources
vm_cores = config.get_int("vmCores") or 2
vm_memory = config.get_int("vmMemory") or 1
vm_core_fraction = config.get_int("vmCoreFraction") or 20
disk_size = config.get_int("diskSize") or 10
disk_type = config.get("diskType") or "network-hdd"

# Security
allow_ssh_from_cidr = config.get("allowSshFromCidr") or "0.0.0.0/0"

# Data source: Find latest Ubuntu 24.04 LTS image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-2404-lts",
)

# VPC Network
network = yandex.VpcNetwork(
    "devops-network",
    name="devops-network-pulumi",
    description="Network for DevOps course lab infrastructure (Pulumi)",
)

# Subnet
subnet = yandex.VpcSubnet(
    "devops-subnet",
    name="devops-subnet-pulumi",
    description="Subnet for DevOps VMs (Pulumi)",
    v4_cidr_blocks=["10.129.0.0/24"],
    zone=zone,
    network_id=network.id,
)

# Security Group (Firewall Rules)
security_group = yandex.VpcSecurityGroup(
    "devops-sg",
    name="devops-security-group-pulumi",
    description="Security group for DevOps VM - allows SSH (Pulumi)",
    network_id=network.id,
    ingress=[
        # Allow SSH
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow SSH",
            v4_cidr_blocks=[allow_ssh_from_cidr],
            port=22,
        ),
        # Allow HTTP
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80,
        ),
        # Allow HTTPS
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow HTTPS",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=443,
        ),
    ],
    egress=[
        # Allow all outbound traffic
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outbound traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535,
        ),
    ],
)

# Cloud-init configuration
cloud_init = f"""#cloud-config
users:
  - name: {vm_user}
    groups: sudo
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh_authorized_keys:
      - {ssh_public_key}
package_update: true
package_upgrade: true
packages:
  - curl
  - wget
  - git
  - vim
runcmd:
  - echo "VM provisioned by Pulumi for DevOps Lab 04" > /etc/motd
"""

# Compute Instance (Virtual Machine)
vm = yandex.ComputeInstance(
    "devops-vm",
    name=vm_name,
    platform_id="standard-v2",
    zone=zone,
    hostname="devops-lab04-pulumi",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=vm_cores,
        memory=vm_memory,
        core_fraction=vm_core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=disk_size,
            type=disk_type,
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,  # Assign public IP
            security_group_ids=[security_group.id],
        )
    ],
    metadata={
        "user-data": cloud_init,
    },
    labels={
        "environment": "lab04",
        "managed_by": "pulumi",
        "purpose": "devops-course",
    },
)

# Exports (Outputs)
pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_fqdn", vm.fqdn)
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("ssh_connection", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {vm_user}@{ip}"
))
pulumi.export("vm_zone", vm.zone)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
