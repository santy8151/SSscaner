from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
import os
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scanner-service")

app = FastAPI(title="SSSCANER Scanner Service", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scanner.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class ScannerLogEntry(Base):
    __tablename__ = "scanner_logs"
    
    id = Column(String, primary_key=True, index=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    data_type = Column(String)
    raw_data = Column(Text)
    interpreted_data = Column(JSON)
    status = Column(String)

class MeasurementRecord(Base):
    __tablename__ = "measurements"
    
    id = Column(String, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    measurement_type = Column(String)
    pressure_suction = Column(Float, nullable=True)
    pressure_discharge = Column(Float, nullable=True)
    temperature_evaporator = Column(Float, nullable=True)
    temperature_condenser = Column(Float, nullable=True)
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    frequency_data = Column(JSON, nullable=True)
    oscilloscope_data = Column(JSON, nullable=True)
    raw_logs = Column(Text)

Base.metadata.create_all(bind=engine)

class MeasurementType(str, Enum):
    FREQUENCY = "frequency"
    AC_MEASUREMENT = "ac_measurement"
    MOTOR_MEASUREMENT = "motor_measurement"
    ENERGY_LEAKAGE = "energy_leakage"

class ScannerDevice(BaseModel):
    device_id: str
    name: str
    connected: bool
    last_connection: Optional[datetime]
    device_type: str

class BluetoothScannerManager:
    def __init__(self):
        self.connected_devices = {}
        self.active_connections = {}
    
    async def discover_devices(self) -> List[Dict[str, Any]]:
        logger.info("Discovering Bluetooth devices...")
        devices = []
        try:
            import bluetooth
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            for addr, name in nearby_devices:
                devices.append({
                    "device_id": addr,
                    "name": name,
                    "type": "bluetooth"
                })
            logger.info(f"Found {len(devices)} devices")
        except Exception as e:
            logger.warning(f"Bluetooth discovery failed: {e}. Using mock devices.")
            devices = [
                {"device_id": "AA:BB:CC:DD:EE:F1", "name": "SSSCANNER-001", "type": "oscilloscope"},
                {"device_id": "AA:BB:CC:DD:EE:F2", "name": "SSSCANNER-002", "type": "pressure_gauge"},
            ]
        
        return devices
    
    async def connect_device(self, device_id: str) -> bool:
        logger.info(f"Connecting to device {device_id}")
        try:
            self.connected_devices[device_id] = {
                "connected": True,
                "timestamp": datetime.utcnow(),
                "buffer": []
            }
            redis_client.set(f"device:{device_id}", "connected", ex=3600)
            logger.info(f"Connected to {device_id}")
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def read_data(self, device_id: str, data_type: str) -> Dict[str, Any]:
        if device_id not in self.connected_devices:
            raise HTTPException(status_code=400, detail="Device not connected")
        
        simulated_data = self._generate_simulated_data(data_type)
        logger.info(f"Read {data_type} from {device_id}")
        return simulated_data
    
    def _generate_simulated_data(self, data_type: str) -> Dict[str, Any]:
        import numpy as np
        
        if data_type == "oscilloscope":
            return {
                "frequency": np.random.uniform(50, 60),
                "amplitude": np.random.uniform(200, 250),
                "waveform": [float(np.sin(x/10)) * 230 for x in range(100)]
            }
        elif data_type == "pressure":
            return {
                "pressure_suction": np.random.uniform(20, 35),
                "pressure_discharge": np.random.uniform(220, 280),
                "temperature": np.random.uniform(40, 50)
            }
        elif data_type == "vacuum":
            return {
                "vacuum_rate": np.random.uniform(-0.5, 0.5),
                "microns": np.random.uniform(100, 500)
            }
        return {}

scanner_manager = BluetoothScannerManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scanner-service"}

@app.get("/api/v1/devices")
async def list_devices():
    devices = await scanner_manager.discover_devices()
    return {"devices": devices}

@app.post("/api/v1/connect")
async def connect(device_id: str):
    success = await scanner_manager.connect_device(device_id)
    if not success:
        raise HTTPException(status_code=500, detail="Connection failed")
    return {"status": "connected", "device_id": device_id}

@app.post("/api/v1/read/{device_id}")
async def read_data(device_id: str, data_type: str, db: Session = Depends(get_db)):
    data = await scanner_manager.read_data(device_id, data_type)
    
    log_entry = ScannerLogEntry(
        id=f"log_{datetime.utcnow().timestamp()}",
        device_id=device_id,
        data_type=data_type,
        raw_data=json.dumps(data),
        interpreted_data=data,
        status="success"
    )
    db.add(log_entry)
    db.commit()
    
    logger.info(f"Logged data from {device_id}: {data_type}")
    return {"data": data, "timestamp": log_entry.timestamp, "log_id": log_entry.id}

@app.get("/api/v1/logs")
async def get_logs(limit: int = 100, device_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ScannerLogEntry)
    if device_id:
        query = query.filter(ScannerLogEntry.device_id == device_id)
    
    logs = query.order_by(ScannerLogEntry.timestamp.desc()).limit(limit).all()
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "device_id": log.device_id,
                "timestamp": log.timestamp,
                "data_type": log.data_type,
                "status": log.status,
                "data": log.interpreted_data
            }
            for log in logs
        ]
    }

@app.post("/api/v1/measurements")
async def save_measurement(
    vehicle_id: str,
    user_id: str,
    measurement_type: MeasurementType,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    measurement = MeasurementRecord(
        id=f"meas_{datetime.utcnow().timestamp()}",
        vehicle_id=vehicle_id,
        user_id=user_id,
        measurement_type=measurement_type.value,
        pressure_suction=data.get("pressure_suction"),
        pressure_discharge=data.get("pressure_discharge"),
        temperature_evaporator=data.get("temperature_evaporator"),
        temperature_condenser=data.get("temperature_condenser"),
        voltage=data.get("voltage"),
        current=data.get("current"),
        frequency_data=data.get("frequency_data"),
        oscilloscope_data=data.get("oscilloscope_data"),
        raw_logs=json.dumps(data)
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    
    logger.info(f"Measurement saved: {measurement.id}")
    return {
        "measurement_id": measurement.id,
        "timestamp": measurement.timestamp,
        "type": measurement_type.value
    }

@app.websocket("/ws/scanner/{device_id}")
async def websocket_scanner(websocket: WebSocket, device_id: str):
    await websocket.accept()
    scanner_manager.active_connections[device_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"WebSocket data from {device_id}: {data}")
            
            processed = {
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": device_id,
                "data": data,
                "status": "received"
            }
            
            await websocket.send_json(processed)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        del scanner_manager.active_connections[device_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
