"""
Sentin-AI Web Dashboard

Real-time monitoring and control interface
Built with FastAPI and WebSockets
"""

from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Sentin-AI Dashboard")

# Set up templates and static files
templates = Jinja2Templates(directory="integration/dashboard/templates")
app.mount("/static", StaticFiles(directory="integration/dashboard/static"), name="static")

# Simulated system state (in production, connect to real sensors)
system_state = {
    "status": "normal",
    "sensors": {
        "uv": {"value": 50, "status": "OK"},
        "voc": {"value": 120, "status": "OK"},
        "temperature": {"value": 22.5, "status": "OK"},
        "humidity": {"value": 45.0, "status": "OK"}
    },
    "ai": {
        "flame_detected": False,
        "confidence": 0.0,
        "last_inference_ms": 0
    },
    "alerts": [],
    "uptime_seconds": 0
}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    return system_state


@app.get("/api/alerts")
async def get_alerts():
    """Get alert history"""
    log_file = Path("logs/alerts.jsonl")
    
    if not log_file.exists():
        return {"alerts": []}
    
    alerts = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                alert = json.loads(line)
                alerts.append(alert)
            except:
                pass
    
    # Return most recent 50 alerts
    return {"alerts": alerts[-50:]}


@app.post("/api/test_alarm")
async def test_alarm():
    """Manual alarm test"""
    # In production, send message to Lizard Brain
    return {
        "success": True,
        "message": "Alarm test triggered",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/calibrate")
async def calibrate_sensors():
    """Trigger sensor calibration"""
    # In production, send calibration command
    return {
        "success": True,
        "message": "Calibration started",
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time sensor updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send current state
            await websocket.send_json(system_state)
            
            # Simulate sensor updates (in production, read from actual sensors)
            import random
            system_state["sensors"]["uv"]["value"] = 50 + random.randint(-10, 10)
            system_state["sensors"]["voc"]["value"] = 120 + random.randint(-20, 20)
            system_state["sensors"]["temperature"]["value"] = 22.5 + random.uniform(-1, 1)
            system_state["uptime_seconds"] += 1
            
            await asyncio.sleep(1)  # 1 Hz update rate
    
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Sentin-AI Web Dashboard")
    print("=" * 60)
    print("\nStarting server...")
    print("Access dashboard at: http://localhost:8080")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
