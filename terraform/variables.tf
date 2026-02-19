# Variables for Yandex Cloud Infrastructure

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  # Get this from: https://console.cloud.yandex.com/cloud
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
  # Get this from: https://console.cloud.yandex.com/cloud
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_key_file" {
  description = "Path to service account key JSON file"
  type        = string
  default     = "key.json"
  # Generate this from: https://console.cloud.yandex.com/iam/service-accounts
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "devops-lab04-vm"
}

variable "vm_user" {
  description = "Default user for SSH access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for VM access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
  # Generate key pair if not exists: ssh-keygen -t rsa -b 4096
}

variable "vm_image_family" {
  description = "OS image family for the VM"
  type        = string
  default     = "ubuntu-2404-lts"
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_memory" {
  description = "RAM in GB"
  type        = number
  default     = 1
}

variable "vm_core_fraction" {
  description = "CPU core fraction (20% for free tier)"
  type        = number
  default     = 20
}

variable "disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "disk_type" {
  description = "Boot disk type"
  type        = string
  default     = "network-hdd"
}

variable "allow_ssh_from_cidr" {
  description = "CIDR block allowed to SSH (your IP for security)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Change to your IP for production!
  # Find your IP: curl ifconfig.me
  # Then set to: "YOUR_IP/32"
}
