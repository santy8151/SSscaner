import logging
import os
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from apps.api.database import (
    AuditLog,
    AuthSession,
    Base,
    ModelRun,
    Organization,
    ScanSession,
    TelemetryRecord,
    User,
    Vehicle,
    build_database,
)
from apps.api.device_routes import build_device_router
from apps.api.lab_routes import build_lab_router
from apps.api.schemas import (
    CalibrationEvaluate,
    Credentials,
    DiagnosticCreate,
    MemberCreate,
    SimulationCreate,
    VehicleCreate,
)
from apps.api.security import hash_password, token_hash, verify_password
from hardware.simulator.vehicle import SCENARIOS, VehicleSimulator
from packages.shared.contracts import TelemetryBatch
from services.calibration.engine import evaluate as evaluate_calibration
from services.diagnosis.engine import evaluate as evaluate_diagnosis
from services.ml.lab import TrainingRunner

load_dotenv()
logger = logging.getLogger("ssscanner")
ROOT = Path(__file__).resolve().parents[2]


def create_app(database_url: str | None = None, environment: str | None = None, rate_limit: int = 120) -> FastAPI:
    mode = environment or os.getenv("APP_ENV", "development")
    if mode not in {"development", "test", "production"}:
        raise RuntimeError("APP_ENV inválido")
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./data/local/ssscanner.db")
    if mode == "production" and not url.startswith("postgresql"):
        raise RuntimeError("Producción requiere PostgreSQL")
    if url == "sqlite:///./data/local/ssscanner.db":
        Path("data/local").mkdir(parents=True, exist_ok=True)
    engine, session_factory = build_database(url)
    runner = TrainingRunner(session_factory, ROOT / "data/local/models")

    @asynccontextmanager
    async def lifespan(app):
        if mode in {"development", "test"} and os.getenv("AUTO_CREATE_SCHEMA", "true").lower() == "true":
            Base.metadata.create_all(engine)
        with session_factory.begin() as db:
            for interrupted in db.scalars(select(ModelRun).where(ModelRun.status.in_(["queued", "running"]))):
                interrupted.status = "interrupted"
                interrupted.result = {"error": "Proceso anterior interrumpido; inicia un nuevo experimento."}
        yield
        runner.shutdown()
        engine.dispose()

    app = FastAPI(title="SSScanner MVP", version="0.1.0", lifespan=lifespan)
    app.state.session_factory = session_factory
    app.state.engine = engine
    app.state.training_runner = runner
    origins = [
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if value.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    requests = defaultdict(deque)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        request.state.request_id = str(uuid4())
        if request.url.path.startswith("/api/"):
            current = time.monotonic()
            auth_route = request.url.path.startswith("/api/v1/auth/")
            key = (request.client.host if request.client else "unknown", auth_route)
            # Expire idle keys; limits are intentionally single-process in this phase.
            for stale in [k for k, q in requests.items() if not q or q[-1] <= current - 60]:
                requests.pop(stale, None)
            queue = requests[key]
            while queue and queue[0] <= current - 60:
                queue.popleft()
            if len(queue) >= (min(rate_limit, 10) if auth_route else rate_limit):
                return JSONResponse(
                    {"detail": "Demasiadas solicitudes", "request_id": request.state.request_id},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            queue.append(current)
            if request.method == "POST":
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > 65536:
                        return JSONResponse({"detail": "Body supera 64 KiB"}, status_code=413)
                request._body = bytes(body)  # Starlette cached request replays this body downstream.
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request_id=%s method=%s path=%s status=%s",
            request.state.request_id,
            request.method,
            request.url.path,
            response.status_code,
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse(
            status_code=422,
            content={"detail": [{"loc": entry["loc"], "msg": entry["msg"]} for entry in error.errors()]},
        )

    @app.exception_handler(IntegrityError)
    async def conflict(request, error):
        return JSONResponse(status_code=409, content={"detail": "El recurso ya existe o la referencia es inválida"})

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request, error):
        logger.error("storage_failure request_id=%s", request.state.request_id)
        return JSONResponse(status_code=503, content={"detail": "Almacenamiento temporalmente no disponible"})

    def db_session():
        with session_factory() as db:
            try:
                yield db
            except Exception:
                db.rollback()
                raise

    def current_user(authorization: str | None = Header(default=None), db=Depends(db_session)):
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "Sesión requerida")
        session = db.get(AuthSession, token_hash(token))
        if not session or session.expires_at <= time.time():
            raise HTTPException(401, "Sesión inválida o expirada")
        user = db.get(User, session.user_id)
        if not user:
            raise HTTPException(401, "Sesión inválida")
        return user

    def technician(user=Depends(current_user)):
        if user.role not in {"admin", "technician"}:
            raise HTTPException(403, "Se requiere rol técnico")
        return user

    def admin(user=Depends(current_user)):
        if user.role != "admin":
            raise HTTPException(403, "Se requiere administrador")
        return user

    def audit(db, user, request, action, resource_id):
        db.add(
            AuditLog(
                organization_id=user.organization_id,
                actor_id=user.id,
                action=action,
                resource_id=resource_id,
                request_id=request.state.request_id,
            )
        )

    def own(db, model, resource_id, user):
        item = db.scalar(select(model).where(model.id == resource_id, model.organization_id == user.organization_id))
        if item is None:
            raise HTTPException(404, "Recurso no encontrado")
        return item

    def user_data(user):
        return {"id": user.id, "email": user.email, "organization_id": user.organization_id, "role": user.role}

    def issue_session(db, user):
        token = secrets.token_urlsafe(32)
        db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=time.time() + 28800))
        return {"access_token": token, "token_type": "bearer", "expires_in": 28800, "user": user_data(user)}

    def serialize(row):
        return {column.name: getattr(row, column.name) for column in row.__table__.columns}

    def scan_data(db, scan):
        batches = db.scalars(
            select(TelemetryRecord)
            .where(TelemetryRecord.scan_id == scan.id, TelemetryRecord.organization_id == scan.organization_id)
            .order_by(TelemetryRecord.created_at.desc())
            .limit(100)
        ).all()
        return {
            **serialize(scan),
            "batches": [batch.payload for batch in reversed(batches)],
            "physical_connection": False,
        }

    @app.get("/health")
    def health():
        return {
            "status": "healthy",
            "service": "ssscanner-api",
            "version": "0.1.0",
            "environment": mode,
            "hardware": "SAMPLE_AND_CLIENT_BLE",
        }

    @app.get("/ready")
    def ready(db=Depends(db_session)):
        db.execute(text("SELECT 1"))
        # Also verify schema exists, not just that the database accepts connections.
        db.execute(select(Organization.id).limit(1))
        return {"status": "ready", "database": engine.dialect.name}

    @app.post("/api/v1/auth/register", status_code=201)
    def register(payload: Credentials, request: Request, db=Depends(db_session)):
        if mode == "production":
            raise HTTPException(403, "Registro público deshabilitado; usar provisión de administrador")
        org = Organization(slug=payload.organization)
        db.add(org)
        db.flush()
        user = User(
            organization_id=org.id, email=payload.email, password_hash=hash_password(payload.password), role="admin"
        )
        db.add(user)
        db.flush()
        audit(db, user, request, "organization.created", org.id)
        result = issue_session(db, user)
        db.commit()
        return result

    @app.post("/api/v1/auth/login")
    def login(payload: Credentials, request: Request, db=Depends(db_session)):
        user = db.scalar(
            select(User)
            .join(Organization)
            .where(Organization.slug == payload.organization, User.email == payload.email)
        )
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(401, "Credenciales inválidas")
        result = issue_session(db, user)
        audit(db, user, request, "auth.login", user.id)
        db.commit()
        return result

    @app.post("/api/v1/auth/logout")
    def logout(request: Request, authorization: str = Header(), user=Depends(current_user), db=Depends(db_session)):
        db.delete(db.get(AuthSession, token_hash(authorization.partition(" ")[2])))
        audit(db, user, request, "auth.logout", user.id)
        db.commit()
        return {"status": "revoked"}

    @app.get("/api/v1/me")
    def me(user=Depends(current_user)):
        return user_data(user)

    @app.post("/api/v1/members", status_code=201)
    def add_member(payload: MemberCreate, request: Request, user=Depends(admin), db=Depends(db_session)):
        member = User(
            organization_id=user.organization_id,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        db.add(member)
        db.flush()
        audit(db, user, request, "member.created", member.id)
        db.commit()
        return user_data(member)

    @app.get("/api/v1/vehicles")
    def vehicles(user=Depends(current_user), db=Depends(db_session)):
        return [
            serialize(row)
            for row in db.scalars(
                select(Vehicle)
                .where(Vehicle.organization_id == user.organization_id)
                .order_by(Vehicle.created_at.desc())
                .limit(100)
            )
        ]

    @app.post("/api/v1/vehicles", status_code=201)
    def create_vehicle(payload: VehicleCreate, request: Request, user=Depends(technician), db=Depends(db_session)):
        vehicle = Vehicle(organization_id=user.organization_id, **payload.model_dump())
        db.add(vehicle)
        db.flush()
        audit(db, user, request, "vehicle.created", vehicle.id)
        db.commit()
        return serialize(vehicle)

    @app.get("/api/v1/simulator/scenarios")
    def scenarios(user=Depends(current_user)):
        return {"origin": "SAMPLE", "scenarios": SCENARIOS, "wire_protocol_emulation": False}

    @app.post("/api/v1/simulator/scans", status_code=201)
    def simulate(payload: SimulationCreate, request: Request, user=Depends(technician), db=Depends(db_session)):
        own(db, Vehicle, payload.vehicle_id, user)
        scan = ScanSession(
            organization_id=user.organization_id,
            vehicle_id=payload.vehicle_id,
            actor_id=user.id,
            origin="SAMPLE",
            protocol=payload.protocol,
            scenario=payload.scenario,
        )
        db.add(scan)
        db.flush()
        batch = VehicleSimulator(payload.scenario, payload.protocol).read_sample(0)
        db.add(
            TelemetryRecord(
                organization_id=user.organization_id,
                scan_id=scan.id,
                idempotency_key=batch.idempotency_key,
                payload=batch.model_dump(mode="json"),
            )
        )
        audit(db, user, request, "sample_scan.created", scan.id)
        db.commit()
        return scan_data(db, scan)

    @app.get("/api/v1/scans")
    def scans(user=Depends(current_user), db=Depends(db_session)):
        return [
            serialize(row)
            for row in db.scalars(
                select(ScanSession)
                .where(ScanSession.organization_id == user.organization_id)
                .order_by(ScanSession.created_at.desc())
                .limit(100)
            )
        ]

    @app.get("/api/v1/scans/{scan_id}")
    def get_scan(scan_id: str, user=Depends(current_user), db=Depends(db_session)):
        return scan_data(db, own(db, ScanSession, scan_id, user))

    @app.post("/api/v1/scans/{scan_id}/telemetry")
    def ingest(
        scan_id: str, payload: TelemetryBatch, request: Request, user=Depends(technician), db=Depends(db_session)
    ):
        scan = own(db, ScanSession, scan_id, user)
        if payload.protocol != scan.protocol or payload.origin != scan.origin:
            raise HTTPException(422, "Protocolo u origen incompatible con la sesión")
        existing = db.scalar(
            select(TelemetryRecord).where(
                TelemetryRecord.scan_id == scan.id, TelemetryRecord.idempotency_key == payload.idempotency_key
            )
        )
        if existing:
            if existing.payload != payload.model_dump(mode="json"):
                raise HTTPException(409, "Clave de idempotencia reutilizada con datos diferentes")
            return {"status": "duplicate", "id": existing.id}
        row = TelemetryRecord(
            organization_id=user.organization_id,
            scan_id=scan.id,
            idempotency_key=payload.idempotency_key,
            payload=payload.model_dump(mode="json"),
        )
        db.add(row)
        db.flush()
        audit(db, user, request, "telemetry.ingested", row.id)
        db.commit()
        return {"status": "stored", "id": row.id}

    @app.post("/api/v1/diagnostics")
    def diagnose(payload: DiagnosticCreate, request: Request, user=Depends(technician), db=Depends(db_session)):
        scan = own(db, ScanSession, payload.scan_id, user)
        batches = scan_data(db, scan)["batches"]
        if not batches:
            raise HTTPException(409, "Sesión sin mediciones")
        result = evaluate_diagnosis(TelemetryBatch.model_validate(batches[-1]))
        audit(db, user, request, "diagnosis.evaluated", scan.id)
        db.commit()
        return {"scan_id": scan.id, **result}

    @app.post("/api/v1/calibration/evaluate")
    def calibration(payload: CalibrationEvaluate, request: Request, user=Depends(technician), db=Depends(db_session)):
        own(db, Vehicle, payload.vehicle_id, user)
        result = evaluate_calibration(payload.vehicle_id)
        audit(db, user, request, "calibration.source_required", payload.vehicle_id)
        db.commit()
        return result

    @app.get("/api/v1/audit")
    def audit_history(user=Depends(admin), db=Depends(db_session)):
        return [
            serialize(row)
            for row in db.scalars(
                select(AuditLog)
                .where(AuditLog.organization_id == user.organization_id)
                .order_by(AuditLog.created_at.desc())
                .limit(100)
            )
        ]

    app.include_router(build_device_router(current_user, technician, db_session, own, audit))
    app.include_router(build_lab_router(current_user, technician, db_session, own, audit, runner))

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    def unknown_api(path: str):
        raise HTTPException(404, "Ruta API no implementada")

    web = ROOT / "apps/web/dist"
    if (web / "assets").exists():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path in {"vision-frame.html", "vision-frame.js"}:
            return FileResponse(web / path)
        routes = {"", "instruments", "models"}
        if path not in routes:
            raise HTTPException(404, "Ruta no encontrada")
        if not (web / "index.html").exists():
            return JSONResponse(
                {
                    "message": "API lista. Ejecuta npm run build en apps/web o inicia Vite en localhost:5173.",
                    "docs": "/docs",
                }
            )
        return FileResponse(web / "index.html")

    return app


app = create_app()
