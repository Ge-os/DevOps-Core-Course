# Terraform configuration for DevOps Lab 04
# Cloud Provider: Yandex Cloud
# Purpose: Provision a VM for Ansible configuration (Lab 05)

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.120.0"
    }
  }
}

# Provider configuration
provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

# Data source: Find latest Ubuntu 24.04 LTS image
data "yandex_compute_image" "ubuntu" {
  family = var.vm_image_family
}

# VPC Network
resource "yandex_vpc_network" "devops_network" {
  name        = "devops-network"
  description = "Network for DevOps course lab infrastructure"
}

# Subnet
resource "yandex_vpc_subnet" "devops_subnet" {
  name           = "devops-subnet"
  description    = "Subnet for DevOps VMs"
  v4_cidr_blocks = ["10.128.0.0/24"]
  zone           = var.zone
  network_id     = yandex_vpc_network.devops_network.id
}

# Security Group (Firewall Rules)
resource "yandex_vpc_security_group" "devops_sg" {
  name        = "devops-security-group"
  description = "Security group for DevOps VM - allows SSH"
  network_id  = yandex_vpc_network.devops_network.id

  # Allow SSH from specified CIDR
  ingress {
    protocol       = "TCP"
    description    = "Allow SSH"
    v4_cidr_blocks = [var.allow_ssh_from_cidr]
    port           = 22
  }

  # Allow HTTP (for future web applications)
  ingress {
    protocol       = "TCP"
    description    = "Allow HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  # Allow HTTPS (for future web applications)
  ingress {
    protocol       = "TCP"
    description    = "Allow HTTPS"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 443
  }

  # Allow all outbound traffic
  egress {
    protocol       = "ANY"
    description    = "Allow all outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

# Compute Instance (Virtual Machine)
resource "yandex_compute_instance" "devops_vm" {
  name        = var.vm_name
  platform_id = "standard-v2"
  zone        = var.zone
  hostname    = "devops-lab04"

  resources {
    cores         = var.vm_cores
    memory        = var.vm_memory
    core_fraction = var.vm_core_fraction # 20% for free tier
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.disk_size
      type     = var.disk_type
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.devops_subnet.id
    nat                = true # Assign public IP
    security_group_ids = [yandex_vpc_security_group.devops_sg.id]
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${file(var.ssh_public_key_path)}"
    user-data = <<-EOT
      #cloud-config
      users:
        - name: ${var.vm_user}
          groups: sudo
          shell: /bin/bash
          sudo: ['ALL=(ALL) NOPASSWD:ALL']
      package_update: true
      package_upgrade: true
      packages:
        - curl
        - wget
        - git
        - vim
      runcmd:
        - echo "VM provisioned by Terraform for DevOps Lab 04" > /etc/motd
    EOT
  }

  labels = {
    environment = "lab04"
    managed_by  = "terraform"
    purpose     = "devops-course"
  }
}
