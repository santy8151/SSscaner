"""Explicit database provisioning. Passwords are entered interactively or via env."""

import argparse
import getpass
import os

from dotenv import load_dotenv
from sqlalchemy import select

from apps.api.database import Base, Organization, User, build_database
from apps.api.schemas import Credentials
from apps.api.security import hash_password


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init-db", "create-admin"])
    parser.add_argument("--organization")
    parser.add_argument("--email")
    args = parser.parse_args()
    url = os.environ["DATABASE_URL"]
    engine, sessions = build_database(url)
    try:
        if args.action == "init-db":
            Base.metadata.create_all(engine)
            print("Esquema inicial creado si no existía. No modifica tablas existentes.")
            return
        if not args.organization or not args.email:
            parser.error("create-admin requiere --organization y --email")
        credentials = Credentials(
            organization=args.organization,
            email=args.email,
            password=os.getenv("BOOTSTRAP_PASSWORD") or getpass.getpass("Contraseña (mínimo 12 caracteres): "),
        )
        with sessions.begin() as db:
            if db.scalar(select(Organization).where(Organization.slug == credentials.organization)):
                raise SystemExit("La organización ya existe; use la API de miembros autenticada.")
            org = Organization(slug=credentials.organization)
            db.add(org)
            db.flush()
            db.add(
                User(
                    organization_id=org.id,
                    email=credentials.email,
                    password_hash=hash_password(credentials.password),
                    role="admin",
                )
            )
        print("Administrador creado. No se imprimen credenciales.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
