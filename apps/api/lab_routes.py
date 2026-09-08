from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select

from apps.api.database import DeviceProfile, DeviceReading, ModelRun, ScanSession, Vehicle
from services.diagnosis.physics import (
    ElectricalRequest,
    PerformanceRequest,
    SignalRequest,
    analyze_signal,
    compare_performance,
    dc_energy,
)
from services.ml.lab import TrainingRequest


def build_lab_router(current_user, technician, db_session, own, audit, runner):
    router = APIRouter(prefix="/api/v1", tags=["BETA and ML lab"])

    @router.post("/physics/frequency")
    def frequency(payload: SignalRequest, user=Depends(current_user)):
        return analyze_signal(payload)

    @router.post("/physics/electrical")
    def electrical(payload: ElectricalRequest, user=Depends(current_user)):
        return dc_energy(payload)

    @router.post("/physics/performance")
    def performance(payload: PerformanceRequest, user=Depends(current_user)):
        return compare_performance(payload)

    def run_data(row):
        return {
            "id": row.id,
            "configuration": row.configuration,
            "status": row.status,
            "progress": row.progress,
            "result": row.result,
            "created_at": row.created_at,
        }

    @router.get("/beta/status")
    def status(user=Depends(current_user), db=Depends(db_session)):
        def count(model):
            return db.scalar(
                select(func.count()).select_from(model).where(model.organization_id == user.organization_id)
            )

        return {
            "stage": "TECHNICAL_BETA",
            "vehicles": count(Vehicle),
            "sample_scans": count(ScanSession),
            "ble_profiles": count(DeviceProfile),
            "browser_ble_packets": count(DeviceReading),
            "model_runs": count(ModelRun),
            "physical_device_attestation": False,
            "oem_sources": 0,
            "machine_control": False,
            "production_ready": False,
        }

    @router.get("/ml/runs")
    def runs(user=Depends(current_user), db=Depends(db_session)):
        return [
            run_data(row)
            for row in db.scalars(
                select(ModelRun)
                .where(ModelRun.organization_id == user.organization_id)
                .order_by(ModelRun.created_at.desc())
                .limit(50)
            )
        ]

    @router.get("/ml/runs/{run_id}")
    def get_run(run_id: str, user=Depends(current_user), db=Depends(db_session)):
        return run_data(own(db, ModelRun, run_id, user))

    @router.post("/ml/runs", status_code=202)
    def train(payload: TrainingRequest, request: Request, user=Depends(technician), db=Depends(db_session)):
        if not runner.reserve():
            raise HTTPException(
                429, "Ya hay un entrenamiento en curso. Espera a que termine.", headers={"Retry-After": "5"}
            )
        try:
            row = ModelRun(
                organization_id=user.organization_id,
                actor_id=user.id,
                configuration=payload.model_dump(),
                status="queued",
                progress=0,
            )
            db.add(row)
            db.flush()
            audit(db, user, request, "sample_model.training_requested", row.id)
            db.commit()
        except Exception:
            runner.slot.release()
            raise
        runner.start(row.id)
        return run_data(row)

    return router
