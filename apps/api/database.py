from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Column,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def new_id():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String(36), primary_key=True, default=new_id)
    slug = Column(String(80), unique=True, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(254), nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)
    __table_args__ = (UniqueConstraint("organization_id", "email"), UniqueConstraint("organization_id", "id"))


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(Float, nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(150), nullable=False)
    kind = Column(String(30), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    created_at = Column(String(40), default=now, nullable=False)
    __table_args__ = (UniqueConstraint("organization_id", "id"),)


class ScanSession(Base):
    __tablename__ = "scan_sessions"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    vehicle_id = Column(String(36), nullable=False)
    actor_id = Column(String(36), nullable=False)
    origin = Column(String(20), nullable=False)
    protocol = Column(String(20), nullable=False)
    scenario = Column(String(40), nullable=False)
    created_at = Column(String(40), default=now, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "vehicle_id"], ["vehicles.organization_id", "vehicles.id"]),
        ForeignKeyConstraint(["organization_id", "actor_id"], ["users.organization_id", "users.id"]),
        UniqueConstraint("organization_id", "id"),
    )


class TelemetryRecord(Base):
    __tablename__ = "telemetry_batches"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    scan_id = Column(String(36), nullable=False)
    idempotency_key = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "scan_id"], ["scan_sessions.organization_id", "scan_sessions.id"]),
        UniqueConstraint("scan_id", "idempotency_key"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(String(80), nullable=False)
    resource_id = Column(String(36), nullable=False)
    request_id = Column(String(36), nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class DeviceProfile(Base):
    __tablename__ = "device_profiles"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    vehicle_id = Column(String(36), nullable=False)
    name = Column(String(150), nullable=False)
    configuration = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["organization_id", "vehicle_id"], ["vehicles.organization_id", "vehicles.id"]),
        UniqueConstraint("organization_id", "id"),
    )


class DeviceReading(Base):
    __tablename__ = "device_readings"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    profile_id = Column(String(36), nullable=False)
    idempotency_key = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "profile_id"], ["device_profiles.organization_id", "device_profiles.id"]
        ),
        UniqueConstraint("profile_id", "idempotency_key"),
    )


class ModelRun(Base):
    __tablename__ = "model_runs"
    id = Column(String(36), primary_key=True, default=new_id)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    configuration = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="queued")
    progress = Column(Integer, nullable=False, default=0)
    result = Column(JSON)
    created_at = Column(String(40), default=now, nullable=False)


def build_database(url: str):
    engine = create_engine(
        url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, pool_pre_ping=True
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine, sessionmaker(bind=engine, expire_on_commit=False)
