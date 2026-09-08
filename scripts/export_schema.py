"""Export the executable phase-one schema as PostgreSQL DDL for review."""

from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from apps.api.database import Base

if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "docs/architecture/schema-phase1.sql"
    statements = [
        str(CreateTable(table).compile(dialect=postgresql.dialect())) + ";" for table in Base.metadata.sorted_tables
    ]
    output.write_text(
        "-- Generated review DDL; not a migration runner. No data or OEM specifications.\n" + "\n\n".join(statements),
        encoding="utf-8",
    )
    print(f"Exported {len(statements)} tables to {output}")
