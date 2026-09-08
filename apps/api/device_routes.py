from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from apps.api.database import DeviceProfile, DeviceReading, Vehicle
from hardware.ble import BLEConfiguration, BLEPacket, DeviceCreate, decode_packet


def build_device_router(current_user, technician, db_session, own, audit):
    router = APIRouter(prefix="/api/v1/devices", tags=["BLE read-only"])

    def profile_data(row):
        return {
            "id": row.id,
            "vehicle_id": row.vehicle_id,
            "name": row.name,
            "configuration": row.configuration,
            "validation_status": "UNVERIFIED_MAPPING",
            "physical_control": False,
        }

    @router.get("")
    def profiles(user=Depends(current_user), db=Depends(db_session)):
        return [
            profile_data(row)
            for row in db.scalars(
                select(DeviceProfile)
                .where(DeviceProfile.organization_id == user.organization_id)
                .order_by(DeviceProfile.created_at.desc())
                .limit(100)
            )
        ]

    @router.post("", status_code=201)
    def create(payload: DeviceCreate, request: Request, user=Depends(technician), db=Depends(db_session)):
        own(db, Vehicle, payload.vehicle_id, user)
        row = DeviceProfile(
            organization_id=user.organization_id,
            vehicle_id=payload.vehicle_id,
            name=payload.name,
            configuration=payload.configuration.model_dump(),
        )
        db.add(row)
        db.flush()
        audit(db, user, request, "ble_profile.created_unverified", row.id)
        db.commit()
        return profile_data(row)

    @router.get("/{profile_id}/readings")
    def readings(profile_id: str, user=Depends(current_user), db=Depends(db_session)):
        own(db, DeviceProfile, profile_id, user)
        return [
            {"id": row.id, **row.payload}
            for row in db.scalars(
                select(DeviceReading)
                .where(DeviceReading.organization_id == user.organization_id, DeviceReading.profile_id == profile_id)
                .order_by(DeviceReading.created_at.desc())
                .limit(50)
            )
        ]

    @router.post("/{profile_id}/readings")
    def ingest(profile_id: str, payload: BLEPacket, request: Request, user=Depends(technician), db=Depends(db_session)):
        profile = own(db, DeviceProfile, profile_id, user)
        config = BLEConfiguration.model_validate(profile.configuration)
        try:
            value = decode_packet(config, payload.raw_hex)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        content = {
            **payload.model_dump(mode="json"),
            "value": value,
            "signal": config.signal,
            "unit": config.unit,
            "validation_status": "UNVERIFIED_MAPPING",
            "provenance": "browser_reported_not_device_attested",
        }
        existing = db.scalar(
            select(DeviceReading).where(
                DeviceReading.profile_id == profile_id, DeviceReading.idempotency_key == payload.idempotency_key
            )
        )
        if existing:
            if existing.payload != content:
                raise HTTPException(409, "Clave reutilizada con datos diferentes")
            return {"id": existing.id, "status": "duplicate", **content}
        row = DeviceReading(
            organization_id=user.organization_id,
            profile_id=profile_id,
            idempotency_key=payload.idempotency_key,
            payload=content,
        )
        db.add(row)
        db.flush()
        audit(db, user, request, "ble_packet.received", row.id)
        db.commit()
        return {"id": row.id, "status": "stored", **content}

    return router
