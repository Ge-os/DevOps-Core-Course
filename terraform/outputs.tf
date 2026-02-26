# Outputs for DevOps Lab 04 Infrastructure

output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.devops_vm.id
}

output "vm_name" {
  description = "Name of the VM"
  value       = yandex_compute_instance.devops_vm.name
}

output "vm_fqdn" {
  description = "Fully qualified domain name of the VM"
  value       = yandex_compute_instance.devops_vm.fqdn
}

output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.devops_vm.network_interface[0].ip_address
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh ${var.vm_user}@${yandex_compute_instance.devops_vm.network_interface[0].nat_ip_address}"
}

output "vm_zone" {
  description = "Zone where VM is deployed"
  value       = yandex_compute_instance.devops_vm.zone
}

output "network_id" {
  description = "ID of the VPC network"
  value       = yandex_vpc_network.devops_network.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.devops_subnet.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = yandex_vpc_security_group.devops_sg.id
}
