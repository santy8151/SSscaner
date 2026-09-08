# Terraform para SSSCANER

Este directorio prepara una máquina EC2 con Ubuntu para ejecutar SSSCANER y Ollama localmente.

## Requisitos

- Terraform instalado
- AWS CLI configurado con credenciales válidas
- clave SSH en AWS

## Uso

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Salida

Terraform mostrará la IP pública de la instancia creada.

## Puertos expuestos

- 22 (SSH)
- 80
- 3000
- 8000
