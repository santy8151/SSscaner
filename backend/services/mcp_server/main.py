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
            "inputSchema": self.input_schema,
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
                        "duration_ms": {"type": "integer", "minimum": 100},
                    },
                    "required": ["device_id", "channel"],
                },
            ),
            self.read_oscilloscope,
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
                    "required": ["device_id", "gauge_type"],
                },
            ),
            self.read_pressure_gauge,
        )

        self.register_tool(
            MCPTool(
                name=MCPToolType.VACUUM_RATE.value,
                description="Read vacuum rate (microns/minute)",
                input_schema={
                    "type": "object",
                    "properties": {"device_id": {"type": "string"}},
                    "required": ["device_id"],
                },
            ),
            self.read_vacuum_rate,
        )

    def register_tool(self, tool: MCPTool, handler: Callable):
        self.tools[tool.name] = tool
        self.handlers[tool.name] = handler

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.handlers:
            raise ValueError(f"Unknown tool: {tool_name}")
        handler = self.handlers[tool_name]
        return await handler(params)

    async def read_oscilloscope(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        channel = params.get("channel", "L")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}", params={"data_type": "oscilloscope"})
                data = response.json()
                return {"success": True, "channel": channel, "data": data.get("data", {}), "timestamp": data.get("timestamp")}
            except Exception as e:
                logger.error(f"Oscilloscope read error: {e}")
                return {"success": False, "error": str(e)}

    async def read_pressure_gauge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        gauge_type = params.get("gauge_type", "suction")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}", params={"data_type": "pressure"})
                data = response.json()
                return {"success": True, "gauge_type": gauge_type, "data": data.get("data", {}), "timestamp": data.get("timestamp")}
            except Exception as e:
                logger.error(f"Pressure read error: {e}")
                return {"success": False, "error": str(e)}

    async def read_vacuum_rate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_id = params.get("device_id")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{SCANNER_SERVICE_URL}/api/v1/read/{device_id}", params={"data_type": "vacuum"})
                data = response.json()
                return {"success": True, "device_id": device_id, "data": data.get("data", {})}
            except Exception as e:
                logger.error(f"Vacuum read error: {e}")
                return {"success": False, "error": str(e)}

registry = ToolRegistry()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-server"}

@app.get("/api/v1/tools")
async def list_tools():
    return {"tools": [tool.to_dict() for tool in registry.tools.values()]}

@app.post("/api/v1/tools/call")
async def call_tool(request: MCPRequest):
    try:
        result = await registry.call_tool(request.method, request.params)
        return MCPResponse(id=request.id, result=result)
    except Exception as exc:
        logger.exception("Tool invocation failed")
        return MCPResponse(id=request.id, result={}, error=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
