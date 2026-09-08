terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_instance" "ssscaner_vm" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.ssscaner_sg.id]

  user_data = <<-EOT
    #!/bin/bash
    set -eux
    apt-get update
    apt-get install -y curl ca-certificates gnupg git python3 python3-pip python3-venv docker.io
    curl -fsSL https://ollama.com/install.sh | sh
    systemctl enable docker
    systemctl start docker
    ollama pull llama3.2
    ollama pull mistral
  EOT

  tags = {
    Name = "ssscaner-vm"
    Project = "SSSCANER"
  }
}

resource "aws_security_group" "ssscaner_sg" {
  name        = "ssscaner-sg"
  description = "Security group for SSSCANER"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "instance_public_ip" {
  value = aws_instance.ssscaner_vm.public_ip
}

output "instance_id" {
  value = aws_instance.ssscaner_vm.id
}
