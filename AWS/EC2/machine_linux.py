#!/usr/bin/env python3
"""
Automatización para preparar una máquina Linux para SSSCANER.

Objetivo:
- detecta el sistema del host
- prepara entorno de desarrollo y ejecución local
- instala Ollama y modelos IA locales
- opcionalmente prepara el entorno virtualizado para poblar la máquina
- ofrece una decisión entre ejecutar en VM o dejarlo en local estático
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def print_banner() -> None:
    print("=" * 80)
    print("SSSCANER - Preparación de máquina Linux")
    print("=" * 80)


def detect_host() -> Dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(command: str, silent: bool = False) -> int:
    print(f"[RUN] {command}")
    result = subprocess.run(command, shell=True, text=True)
    if not silent and result.stdout:
        print(result.stdout)
    if not silent and result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def ensure_apt_packages() -> None:
    print("[INFO] Instalando paquetes base del sistema...")
    commands = [
        "sudo apt-get update",
        "sudo apt-get install -y curl ca-certificates gnupg git python3 python3-pip python3-venv build-essential",
    ]
    for cmd in commands:
        if run_command(cmd) != 0:
            print(f"[WARN] Falló la instalación con: {cmd}")
            break


def install_ollama() -> None:
    if command_exists("ollama"):
        print("[OK] Ollama ya está instalado.")
        return

    print("[INFO] Instalando Ollama...")
    cmd = "curl -fsSL https://ollama.com/install.sh | sh"
    if run_command(cmd) != 0:
        print("[WARN] No se pudo instalar Ollama automáticamente.")


def pull_default_models() -> None:
    if not command_exists("ollama"):
        print("[WARN] Ollama no está disponible; se omite pull de modelos.")
        return

    models = ["llama3.2", "mistral"]
    for model in models:
        print(f"[INFO] Descargando modelo local: {model}")
        run_command(f"ollama pull {model}")


def install_python_dependencies(project_root: Path) -> None:
    requirements = project_root / "requirements.txt"
    if not requirements.exists():
        print("[WARN] No existe requirements.txt en la raíz del proyecto.")
        return

    print("[INFO] Instalando dependencias Python del proyecto...")
    venv_dir = project_root / ".venv"
    if not venv_dir.exists():
        run_command(f"python3 -m venv {venv_dir}")

    pip_path = venv_dir / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
    run_command(f"{pip_path} install -r {requirements}")


def prepare_node_frontend(project_root: Path) -> None:
    frontend_dir = project_root / "frontend"
    if not frontend_dir.exists():
        print("[WARN] No existe el directorio frontend.")
        return

    print("[INFO] Instalando dependencias del frontend...")
    run_command(f"cd {frontend_dir} && npm install")


def setup_docker_if_needed() -> None:
    if command_exists("docker"):
        print("[OK] Docker ya está disponible.")
        return

    print("[INFO] Docker no está instalado: se recomienda instalar Docker Engine o Docker Desktop.")
    print("[INFO] En Ubuntu: sudo apt-get install -y docker.io")


def project_summary(project_root: Path) -> None:
    print("[INFO] Resumen del proyecto:")
    print(f"  - Raíz: {project_root}")
    print(f"  - Docker Compose: {(project_root / 'docker-compose.yml').exists()}")
    print(f"  - Frontend: {(project_root / 'frontend').exists()}")
    print(f"  - Backend: {(project_root / 'backend').exists()}")
    print(f"  - AWS: {(project_root / 'AWS').exists()}")


def prompt_for_mode() -> str:
    while True:
        answer = input("¿Quieres abrir la máquina virtual o dejarla en local estático? [vm/local]: ").strip().lower()
        if answer in {"vm", "v"}:
            return "vm"
        if answer in {"local", "l"}:
            return "local"
        print("Respuesta inválida. Usa 'vm' o 'local'.")


def generate_vm_guidance() -> None:
    print("\n[INFO] Guía para VM con Ubuntu + Ollama")
    print("1) Instala Oracle VirtualBox")
    print("2) Crea una VM con Ubuntu 24.04 LTS x64")
    print("3) Asigna 8 GB RAM y 4 CPU mínimo")
    print("4) En la VM ejecuta estos comandos:")
    print("   sudo apt-get update")
    print("   sudo apt-get install -y curl ca-certificates gnupg git python3 python3-pip python3-venv")
    print("   curl -fsSL https://ollama.com/install.sh | sh")
    print("   ollama pull llama3.2")
    print("   ollama pull mistral")
    print("5) Luego ejecuta el proyecto con:")
    print("   git clone <repo>")
    print("   cd ssscaner")
    print("   python3 -m venv .venv")
    print("   . .venv/bin/activate")
    print("   pip install -r requirements.txt")
    print("   docker compose up --build")


def generate_local_guidance(project_root: Path) -> None:
    print("\n[INFO] Guía para entorno local estático")
    print("Ejecuta esto en esta máquina:")
    print(f"  cd {project_root}")
    print("  python3 -m venv .venv")
    print("  . .venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  curl -fsSL https://ollama.com/install.sh | sh")
    print("  ollama pull llama3.2")
    print("  ollama pull mistral")
    print("  docker compose up --build")
    print("\n[Terraform] Para aprovisionar infra con Terraform: cd terraform && terraform init && terraform apply")


def main() -> int:
    print_banner()
    host = detect_host()
    print(f"[INFO] Host detectado: {host}")

    project_root = Path(__file__).resolve().parents[1]
    project_summary(project_root)

    ensure_apt_packages()
    install_ollama()
    pull_default_models()
    install_python_dependencies(project_root)
    prepare_node_frontend(project_root)
    setup_docker_if_needed()

    mode = prompt_for_mode()
    if mode == "vm":
        generate_vm_guidance()
    else:
        generate_local_guidance(project_root)

    print("\n[OK] Configuración terminada. Revisa la guía final para ejecutar el proyecto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
