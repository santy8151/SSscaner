from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(title="SSSCANER API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8003")
SCANNER_SERVICE_URL = os.getenv("SCANNER_SERVICE_URL", "http://localhost:8002")

async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/auth/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/auth/register")
async def register(email: str, password: str, name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/v1/auth/register",
            json={"email": email, "password": password, "name": name}
        )
        return response.json()

@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        return response.json()

@app.post("/api/v1/ml/diagnose")
async def diagnose(vehicle_id: str, measurements: Dict[str, Any], user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/diagnose",
            json={"vehicle_id": vehicle_id, "measurements": measurements, "user_id": user.get("user_id")}
        )
        return response.json()

@app.get("/api/v1/ml/nodes")
async def get_nodes(user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ML_SERVICE_URL}/api/v1/nodes")
        return response.json()

@app.post("/api/v1/ml/train-node")
async def train_node(node_id: str, epochs: int, algorithm: str, user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/nodes/{node_id}/train",
            json={"epochs": epochs, "algorithm": algorithm}
        )
        return response.json()

@app.get("/api/v1/scanner/devices")
async def get_scanner_devices(user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SCANNER_SERVICE_URL}/api/v1/devices")
        return response.json()

@app.post("/api/v1/scanner/connect")
async def connect_scanner(device_id: str, user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SCANNER_SERVICE_URL}/api/v1/connect",
            json={"device_id": device_id}
        )
        return response.json()

@app.get("/api/v1/scanner/logs")
async def get_scanner_logs(limit: int = 100, user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SCANNER_SERVICE_URL}/api/v1/logs",
            params={"limit": limit}
        )
        return response.json()

@app.get("/api/v1/vehicle/{vehicle_id}")
async def get_vehicle(vehicle_id: str, user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ML_SERVICE_URL}/api/v1/vehicles/{vehicle_id}"
        )
        return response.json()

@app.post("/api/v1/vehicle")
async def create_vehicle(vehicle_data: Dict[str, Any], user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/v1/vehicles",
            json={**vehicle_data, "user_id": user.get("user_id")}
        )
        return response.json()

@app.get("/api/v1/diagnostics/history/{vehicle_id}")
async def get_diagnostics_history(vehicle_id: str, limit: int = 20, user=Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ML_SERVICE_URL}/api/v1/diagnostics/history/{vehicle_id}",
            params={"limit": limit}
        )
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
