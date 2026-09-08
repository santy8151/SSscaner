#!/usr/bin/env python3
"""
Automatización para preparar un entorno local o VM para SSSCANER.

Qué hace:
- recopila una vista rápida del proyecto para debugging
- detecta el sistema operativo y arquitectura del host
- recomienda la mejor versión de Linux para esa máquina
- instala Oracle VirtualBox si no está disponible
- prepara la descarga/instalación de Ollama y modelos locales
- pregunta si debe abrir la máquina virtual o dejarlo en modo local estático

Uso:
    python Automatition.py
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def print_banner() -> None:
    print("=" * 80)
    print("SSSCANER - Automatización de entorno local / VM")
    print("=" * 80)


def detect_host() -> Dict[str, str]:
    system = platform.system().lower()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()

    if system == "windows":
        os_name = "windows"
    elif system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "macos"
    else:
        os_name = "unknown"

    return {
        "system": system,
        "os_name": os_name,
        "release": release,
        "version": version,
        "machine": machine,
    }


def recommend_linux_distro(host: Dict[str, str]) -> str:
    arch = host["machine"].lower()
    if "arm" in arch or "aarch" in arch:
        if host["os_name"] == "windows":
            return "Ubuntu 24.04 LTS ARM64"
        return "Ubuntu 24.04 LTS ARM64"

    if host["os_name"] == "windows":
        return "Ubuntu 24.04 LTS x64"

    return "Ubuntu 24.04 LTS x64"


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    project_root = current.parent
    if (project_root / "docker-compose.yml").exists():
        return project_root
    if (current / "docker-compose.yml").exists():
        return current
    return project_root


def collect_project_debug(project_root: Path) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "project_root": str(project_root),
        "python_files": [],
        "docker_files": [],
        "frontend_files": [],
        "backend_files": [],
        "notes": [],
    }

    for path in sorted(project_root.rglob("*.py")):
        summary["python_files"].append(str(path.relative_to(project_root)))

    for path in sorted(project_root.rglob("docker-compose.yml")):
        summary["docker_files"].append(str(path.relative_to(project_root)))

    for path in sorted(project_root.rglob("package.json")):
        summary["frontend_files"].append(str(path.relative_to(project_root)))

    for path in sorted(project_root.rglob("*.yaml")):
        summary["backend_files"].append(str(path.relative_to(project_root)))

    summary["notes"].append("Proyecto detectado para levantar un entorno local o VM.")
    summary["notes"].append("Se recomienda usar Ubuntu 24.04 LTS para evitar incompatibilidades con Ollama y modelos locales.")

    debug_file = project_root / "project_debug_summary.json"
    debug_file.write("\n".join([json.dumps(summary, indent=2)]) + "\n", encoding="utf-8")
    print(f"[OK] Resumen de debugging guardado en: {debug_file}")
    return summary


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_shell(command: str, silent: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if not silent:
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
    return result


def install_virtualbox_windows() -> bool:
    print("[INFO] Comprobando si Oracle VirtualBox está instalado...")
    if command_exists("VBoxManage"):
        print("[OK] VirtualBox ya está disponible.")
        return True

    if command_exists("winget"):
        print("[INFO] Instalando Oracle VirtualBox con winget...")
        result = run_shell(
            "winget install --id Oracle.VirtualBox --accept-source-agreements --accept-package-agreements -e",
            silent=False,
        )
        return result.returncode == 0

    print("[WARN] No se encontró winget. Descarga VirtualBox manualmente desde:")
    print("https://www.virtualbox.org/wiki/Downloads")
    return False


def get_linux_install_commands(distro: str) -> List[str]:
    base_commands = [
        "sudo apt-get update",
        "sudo apt-get install -y curl ca-certificates gnupg",
        "curl -fsSL https://ollama.com/install.sh | sh",
        "ollama serve &",
        "ollama pull llama3.2",
        "ollama pull mistral",
        "sudo apt-get install -y python3 python3-pip git docker.io",
        "python3 -m pip install --upgrade pip",
        "pip install fastapi uvicorn redis sqlalchemy psycopg2-binary",
        "git clone https://github.com/your-org/ssscaner.git /workspace/ssscaner",
    ]
    return [
        f"# Sistema recomendado: {distro}",
        *base_commands,
    ]


def create_vm_setup_script(project_root: Path, distro: str) -> Path:
    script_path = project_root / "setup_vm_ssscaner.sh"
    script_content = f"""#!/usr/bin/env bash
set -e

# Ubuntu / Linux recomendado para la VM
# Distro sugerida: {distro}

sudo apt-get update
sudo apt-get install -y curl ca-certificates gnupg git python3 python3-pip docker.io

curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2
ollama pull mistral

cd /workspace || mkdir -p /workspace
if [ ! -d /workspace/ssscaner ]; then
  git clone https://github.com/your-org/ssscaner.git /workspace/ssscaner
fi

cd /workspace/ssscaner
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

printf '\n========================================\n'
printf 'Entorno preparado para SSSCANER en VM\n'
printf 'Lanza el proyecto con:\n'
printf '  docker compose up --build\n'
printf '  o\n'
printf '  uvicorn backend.services.api-gateway.main:app --host 0.0.0.0 --port 8000\n'
printf '========================================\n'
"""
    script_path.write_text(script_content, encoding="utf-8")
    os.chmod(script_path, 0o755)
    print(f"[OK] Script de la VM generado: {script_path}")
    return script_path


def prompt_for_vm_or_local() -> str:
    while True:
        answer = input("¿Quieres abrir la máquina virtual con Ubuntu + Ollama? [s/N]: ").strip().lower()
        if answer in {"", "n", "no"}:
            return "local"
        if answer in {"s", "si", "yes", "y"}:
            return "vm"
        print("Respuesta no válida. Escribe 's' para sí o 'n' para no.")


def create_vm_with_virtualbox(project_root: Path, distro: str) -> None:
    print("[INFO] Preparando la VM con VirtualBox...")
    script_path = create_vm_setup_script(project_root, distro)
    print("\nComandos recomendados para crear la VM en VirtualBox:")
    print("1) Crear la máquina virtual:")
    print("   VBoxManage createvm --name SSSCANER-UBUNTU --register")
    print("2) Configurar RAM, CPU y red:")
    print("   VBoxManage modifyvm SSSCANER-UBUNTU --memory 8192 --cpus 4 --nic1 nat")
    print("3) Crear disco y arrancar ISO:")
    print("   VBoxManage createhd --filename SSSCANER-UBUNTU.vdi --size 200000")
    print("   VBoxManage storagectl SSSCANER-UBUNTU --name SATA --add sata --controller IntelAhci")
    print("   VBoxManage storageattach SSSCANER-UBUNTU --storagectl SATA --port 0 --device 0 --type hdd --medium SSSCANER-UBUNTU.vdi")
    print("4) Ejecutar la ISO de Ubuntu recién descargada:")
    print("   VBoxManage startvm SSSCANER-UBUNTU")
    print(f"\n5) Dentro de la VM, ejecutar el script preparado:")
    print(f"   sudo bash {script_path.name}")
    print("\n[NOTE] Si no quieres abrir una MV, el flujo local estático está disponible.")
    print("\n[Terraform] También puedes provisionar infraestructura con Terraform en la carpeta terraform/.")


def configure_static_local(project_root: Path, distro: str) -> None:
    print("[INFO] Modo local estático activado.")
    print(f"[INFO] Distro recomendada: {distro}")
    print("\nInstalación recomendada para PC host:")
    print("- Python 3.11+")
    print("- Git")
    print("- Node 20+")
    print("- Ollama")
    print("- Docker Desktop o Docker Engine (si se usa Compose)")
    print("\nComandos sugeridos:")
    print("  python -m venv .venv")
    print("  .\\.venv\\Scripts\\activate  (Windows)")
    print("  pip install -r requirements.txt")
    print("  curl -fsSL https://ollama.com/install.sh | sh")
    print("  ollama pull llama3.2")
    print("  ollama pull mistral")
    print("\nLuego puedes correr:")
    print("  docker compose up --build")
    print("  o")
    print("  uvicorn backend.services.api-gateway.main:app --host 0.0.0.0 --port 8000 --reload")


def main() -> int:
    print_banner()
    host = detect_host()
    print(f"[INFO] Host detectado: {host}")

    project_root = find_project_root()
    print(f"[INFO] Proyecto base: {project_root}")
    collect_project_debug(project_root)

    distro = recommend_linux_distro(host)
    print(f"[INFO] Linux recomendado: {distro}")

    if host["os_name"] == "windows":
        install_virtualbox_windows()

    choice = prompt_for_vm_or_local()

    if choice == "vm":
        create_vm_with_virtualbox(project_root, distro)
    else:
        configure_static_local(project_root, distro)

    print("\n[OK] Automatización finalizada. Revisa la ruta del resumen del proyecto y decide el flujo correcto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
