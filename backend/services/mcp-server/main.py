from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Callable, Awaitable
import json
import logging
import os
import httpx
from datetime import datetime
from enum import Enum
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

app = FastAPI(title="SSSCANER MCP Server", version="1.0.0")

SCANNER_SERVICE_URL = os.getenv("SCANNER_SERVICE_URL", "http://localhost:8002")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8003")

class MCPToolType(str, Enum):
    OSCILLOSCOPE = "read_oscilloscope_fft"
    PRESSURE_GAUGE = "read_pressure_gauge"
    VACUUM_RATE = "read_vacuum_rate"
    PREDICT_FAULT = "predict_fault"
    GET_RECOMMENDATIONS = "get_recommendations"
    GENERATE_DIAGRAM = "generate_vehicle_diagram"
    GET_VEHICLE_INFO = "get_vehicle_info"

class MCPRequest(BaseModel):
    id: str
    method: str
    params: Dict[str, Any]

class MCPResponse(BaseModel):
    id: str
    result: Dict[str, Any]
    error: Optional[str] = None

class MCPTool:
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}
        self._register_tools()
    
    def _register_tools(self):
        self.register_tool(
            MCPTool(
                name=MCPToolType.OSCILLOSCOPE.value,
                description="Read oscilloscope FFT data from connected device",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Device identifier"},
                        "channel": {"type": "string", "enum": ["L", "N", "PE"]},
                        "duration_ms": {"type": "integer", "minimum": 100}
                    },
                    "required": ["device_id", "channel"]
                }
            ),
            self.read_oscilloscope
        )
        
        self.register_tool(
            MCPTool(
                name=MCPToolType.PRESSURE_GAUGE.value,
                description="Read pressure gauge data (PSI)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                        "gauge_type": {"type": "string", "enum": ["suction", "discharge", "vacuum"]},
                    },
                    "required": ["device_id", "gauge_type"]
                }
            ),
            self.read_pressure_gauge
        )
        
        self.register_tool(
            MCPTool(
                name=MCPToolType.VACUUM_RATE.value,
                description="Read vacuum rate (microns/minute)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string"},
                    },
                    "required": ["device_id"]
                }
            ),
            self.read_vacuum_rate
        )
        
        self.register_tool(
            MCPTool(
                name=MCPToolType.PREDICT_FAULT.value,
                description="Use ML model to predict potential faults",
                input_schema={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "string"},
                        "measurements": {"type": "object"}
                    },
                    "required": ["vehicle_id", "measurements"]
                }
            ),
            self.predict_fault
        )
        
        self.register_tool(
            MCPTool(
                name=MCPToolType.GENERATE_DIAGRAM.value,
                description="Generate vehicle diagram using HuggingFace or NanoBanana",
                input_schema={
                    "type": "object",
                    "properties": {
                        "vehicle_model": {"type": "string"},
                        "fault_location": {"type": "string"},
                    },
                    "required": ["vehicle_model"]
                }
            ),
            self.generate_diagram
        )
        
        self.register_tool(
            MCPTool(
                name=MCPToolType.GET_VEHICLE_INFO.value,
                description="Get vehicle information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "string"},
                    },
                    "required": ["vehicle_id"]
                }
            ),
            self.get_vehicle_info
        )
    
    def register_tool(self, tool: MCPTool, handler: Callable):
        self.tools[tool.name] = tool
        self.handlers[tool.name] = handler
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.handlers:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.handlers[tool_name]
        result = await handler(params)
        return result
    
    async def read_oscilloscope(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        channel = params.get("channel", "L")
        duration = params.get("duration_ms", 1000)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}",
                    params={"data_type": "oscilloscope"}
                )
                data = response.json()
                logger.info(f"Oscilloscope read from {device_id}: {channel}")
                return {
                    "success": True,
                    "channel": channel,
                    "data": data.get("data", {}),
                    "timestamp": data.get("timestamp")
                }
            except Exception as e:
                logger.error(f"Oscilloscope read error: {e}")
                return {"success": False, "error": str(e)}
    
    async def read_pressure_gauge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        gauge_type = params.get("gauge_type", "suction")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}",
                    params={"data_type": "pressure"}
                )
                data = response.json()
                logger.info(f"Pressure gauge read: {gauge_type}")
                return {
                    "success": True,
                    "gauge_type": gauge_type,
                    "data": data.get("data", {}),
                    "unit": "PSI"
                }
            except Exception as e:
                logger.error(f"Pressure gauge read error: {e}")
                return {"success": False, "error": str(e)}
    
    async def read_vacuum_rate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}",
                    params={"data_type": "vacuum"}
                )
                data = response.json()
                logger.info(f"Vacuum rate read from {device_id}")
                return {
                    "success": True,
                    "vacuum_rate": data.get("data", {}).get("vacuum_rate"),
                    "microns": data.get("data", {}).get("microns"),
                    "unit": "microns/minute"
                }
            except Exception as e:
                logger.error(f"Vacuum rate read error: {e}")
                return {"success": False, "error": str(e)}
    
    async def predict_fault(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vehicle_id = params.get("vehicle_id")
        measurements = params.get("measurements", {})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{ML_SERVICE_URL}/api/v1/diagnose",
                    params={"vehicle_id": vehicle_id},
                    json={"measurements": measurements}
                )
                data = response.json()
                logger.info(f"Fault prediction for {vehicle_id}")
                return {
                    "success": True,
                    "diagnostics": data.get("diagnostics", []),
                    "critical_count": data.get("critical_count", 0)
                }
            except Exception as e:
                logger.error(f"Fault prediction error: {e}")
                return {"success": False, "error": str(e)}
    
    async def generate_diagram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vehicle_model = params.get("vehicle_model", "Generic Vehicle")
        fault_location = params.get("fault_location", "AC System")
        
        logger.info(f"Generating diagram for {vehicle_model}: {fault_location}")
        
        return {
            "success": True,
            "diagram_url": f"https://via.placeholder.com/1024?text=Diagram+{vehicle_model}",
            "vehicle_model": vehicle_model,
            "location": fault_location,
            "service": "placeholder"
        }
    
    async def get_vehicle_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        vehicle_id = params.get("vehicle_id")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{ML_SERVICE_URL}/api/v1/vehicles/{vehicle_id}"
                )
                data = response.json()
                logger.info(f"Vehicle info retrieved: {vehicle_id}")
                return {
                    "success": True,
                    "vehicle": data
                }
            except Exception as e:
                logger.error(f"Get vehicle info error: {e}")
                return {"success": False, "error": str(e)}

registry = ToolRegistry()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-server"}

@app.get("/mcp/tools")
async def list_tools():
    return {
        "tools": [tool.to_dict() for tool in registry.tools.values()]
    }

@app.post("/mcp/call")
async def call_tool(request: MCPRequest) -> MCPResponse:
    try:
        result = await registry.call_tool(request.method, request.params)
        return MCPResponse(id=request.id, result=result)
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return MCPResponse(id=request.id, result={}, error=str(e))

@app.websocket("/mcp/ws")
async def websocket_mcp(websocket: WebSocket):
    await websocket.accept()
    logger.info("MCP WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            
            response = await call_tool(MCPRequest(**request))
            
            await websocket.send_text(response.model_dump_json())
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
