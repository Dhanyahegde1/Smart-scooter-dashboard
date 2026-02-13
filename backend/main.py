from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import uvicorn
from model import LSTMAutoencoder
import joblib
import random
from pydantic import BaseModel

# System State Enum
class SystemState(str, Enum):
    NORMAL = "NORMAL"
    ATTACK_DETECTED = "ATTACK_DETECTED"
    SAFE_MODE = "SAFE_MODE"
    ATTACK_SIMULATION = "ATTACK_SIMULATION"

# Pydantic models
class AttackRequest(BaseModel):
    attack_type: str
    timestamp: Optional[str] = None

class AttackResponse(BaseModel):
    status: str
    message: str
    anomaly_score: float
    countdown: Optional[int] = None
    state: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.state_history: List[Dict] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass
    
    def add_state_history(self, state_data: dict):
        self.state_history.append({
            **state_data,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 1000 entries
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]

# Global state
system_state = SystemState.NORMAL
anomaly_score = 0.0
reconstruction_error = 0.0
safe_mode_timer = None
attack_timeline = []
ml_model = None
connection_manager = ConnectionManager()
telemetry_buffer = []

# Shared state for admin dashboard
shared_state = {
    "system_state": system_state.value,
    "anomaly_score": anomaly_score,
    "reconstruction_error": reconstruction_error,
    "threshold": 0.8,
    "safe_mode_countdown": None,
    "attack_timeline": attack_timeline,
    "telemetry_history": [],
    "ml_decisions": [],
    "ml_connected": False,
    "last_update": datetime.now().isoformat()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global ml_model
    print("Loading ML model...")
    try:
        ml_model = LSTMAutoencoder()
        # Try to load pre-trained model
        import os
        if os.path.exists('models/lstm_autoencoder.h5'):
            from tensorflow.keras.models import load_model
            ml_model.model = load_model('models/lstm_autoencoder.h5')
            ml_model.scaler = joblib.load('models/scaler.pkl')
            print("ML model loaded successfully")
            shared_state["ml_connected"] = True
        else:
            print("No pre-trained model found. Using default.")
            # Train a simple model for demo
            ml_model.build_model()
            # Generate some training data
            X_train = np.random.randn(100, 10, 6)
            ml_model.fit(X_train, epochs=10)
            shared_state["ml_connected"] = True
    except Exception as e:
        print(f"Error loading model: {e}")
        shared_state["ml_connected"] = False
    
    # Start background task for state management
    asyncio.create_task(state_manager())
    
    yield
    
    # Cleanup
    print("Shutting down...")

app = FastAPI(lifespan=lifespan, title="Smart Scooter ML Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_shared_state():
    """Update shared state for all components"""
    shared_state.update({
        "system_state": system_state.value,
        "anomaly_score": anomaly_score,
        "reconstruction_error": reconstruction_error,
        "safe_mode_countdown": safe_mode_timer,
        "attack_timeline": attack_timeline,
        "last_update": datetime.now().isoformat(),
        "ml_connected": ml_model is not None
    })

async def trigger_safe_mode():
    """Trigger safe mode - called by ML model decision"""
    global system_state, safe_mode_timer
    
    system_state = SystemState.SAFE_MODE
    safe_mode_timer = 0
    
    # Log attack timeline
    attack_timeline.append({
        "event": "SAFE_MODE_ACTIVATED",
        "timestamp": datetime.now().isoformat(),
        "trigger": "ML_MODEL_DECISION",
        "anomaly_score": anomaly_score
    })
    
    update_shared_state()
    
    # Broadcast to all connected clients
    await connection_manager.broadcast({
        "type": "SYSTEM_STATE",
        "state": system_state.value,
        "message": "SAFE MODE ACTIVATED - ML detected critical anomaly",
        "timestamp": datetime.now().isoformat(),
        "anomaly_score": anomaly_score
    })
    
    print("SAFE MODE ACTIVATED by ML model")

async def simulate_attack_with_ml(attack_type: str):
    """Simulate attack and get anomaly score from ML"""
    global anomaly_score, reconstruction_error, system_state, safe_mode_timer
    
    try:
        # Generate abnormal telemetry based on attack type
        if attack_type.lower() == "gps":
            abnormal_data = [80, 5.0, 5.0, 15.0, 0.5, 0.5]  # GPS spoofing
        elif attack_type.lower() == "speed":
            abnormal_data = [200, 20.0, 20.0, 30.0, 0.01, 0.01]  # Speed injection
        elif attack_type.lower() == "pattern":
            abnormal_data = [150, 15.0, -15.0, 25.0, 1.0, -1.0]  # Pattern anomaly
        elif attack_type.lower() == "emergency":
            abnormal_data = [300, 50.0, 50.0, 50.0, 2.0, 2.0]  # Emergency attack
        else:
            abnormal_data = [100, 10.0, 10.0, 20.0, 0.1, 0.1]  # Generic attack
        
        # Create sequence for ML model (10 timesteps)
        telemetry_sequence = []
        for i in range(10):
            # Add some variation to the sequence
            varied_data = [x + random.uniform(-0.1, 0.1) * x for x in abnormal_data]
            telemetry_sequence.append(varied_data)
        
        data_array = np.array(telemetry_sequence)
        
        if ml_model and ml_model.model is not None:
            # Get anomaly score from ML model
            ml_score, mse, _ = ml_model.predict_anomaly(data_array)
            anomaly_score = ml_score
            reconstruction_error = mse
            
            print(f"ML Anomaly Score for {attack_type}: {anomaly_score:.3f}")
        else:
            # Fallback to simulated score
            if attack_type.lower() == "gps":
                anomaly_score = 0.85 + random.random() * 0.1
            elif attack_type.lower() == "speed":
                anomaly_score = 0.75 + random.random() * 0.15
            elif attack_type.lower() == "pattern":
                anomaly_score = 0.9 + random.random() * 0.05
            elif attack_type.lower() == "emergency":
                anomaly_score = 0.95
            else:
                anomaly_score = 0.7 + random.random() * 0.2
            reconstruction_error = anomaly_score * 0.1
            
            print(f"Simulated Anomaly Score for {attack_type}: {anomaly_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"Error in ML simulation: {e}")
        # Fallback to default scores
        anomaly_score = 0.8 + random.random() * 0.15
        reconstruction_error = anomaly_score * 0.1
        return True

async def start_attack_simulation(attack_type: str):
    """Start attack simulation with 6-second countdown"""
    global system_state, safe_mode_timer
    
    if system_state == SystemState.SAFE_MODE:
        return False
    
    # Set to attack simulation state
    system_state = SystemState.ATTACK_SIMULATION
    safe_mode_timer = 6  # 6-second countdown
    
    # Log attack simulation
    attack_timeline.append({
        "event": "ATTACK_SIMULATION_STARTED",
        "timestamp": datetime.now().isoformat(),
        "attack_type": attack_type,
        "countdown": safe_mode_timer
    })
    
    update_shared_state()
    
    # Broadcast attack simulation start
    await connection_manager.broadcast({
        "type": "ATTACK_SIMULATION",
        "attack_type": attack_type,
        "anomaly_score": anomaly_score,
        "countdown": safe_mode_timer,
        "message": f"{attack_type} attack simulated. Switching to safe mode in {safe_mode_timer} seconds"
    })
    
    print(f"{attack_type} attack simulation started. Countdown: {safe_mode_timer}s")
    return True

async def detect_anomaly(telemetry_data: List[float]):
    """Run ML inference and detect anomalies"""
    global anomaly_score, reconstruction_error, system_state, safe_mode_timer
    
    try:
        # Add to buffer
        telemetry_buffer.append(telemetry_data)
        if len(telemetry_buffer) > 10:
            telemetry_buffer.pop(0)
        
        # Need at least 10 timesteps for ML model
        if len(telemetry_buffer) == 10:
            data_array = np.array(telemetry_buffer)
            
            if ml_model and ml_model.model is not None:
                # Get anomaly score from ML model
                ml_score, mse, _ = ml_model.predict_anomaly(data_array)
                anomaly_score = ml_score
                reconstruction_error = mse
                
                # Update shared state
                shared_state["telemetry_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "data": telemetry_data,
                    "anomaly_score": anomaly_score,
                    "reconstruction_error": mse
                })
                
                # ML Decision Logic
                if anomaly_score > 0.7 and system_state == SystemState.NORMAL:
                    # Attack detected
                    system_state = SystemState.ATTACK_DETECTED
                    safe_mode_timer = 6  # 6 second countdown
                    
                    attack_timeline.append({
                        "event": "ATTACK_DETECTED",
                        "timestamp": datetime.now().isoformat(),
                        "anomaly_score": anomaly_score,
                        "threshold": ml_model.threshold,
                        "trigger": "ML_INFERENCE"
                    })
                    
                    # Broadcast attack detection
                    await connection_manager.broadcast({
                        "type": "ATTACK_DETECTED",
                        "anomaly_score": anomaly_score,
                        "countdown": safe_mode_timer,
                        "message": f"ML detected anomaly! Safe mode in {safe_mode_timer}s"
                    })
                    
                    print(f"ATTACK DETECTED by ML! Score: {anomaly_score:.2f}")
                    
                elif anomaly_score > 0.9 and system_state == SystemState.ATTACK_DETECTED:
                    # Immediate safe mode for critical anomalies
                    await trigger_safe_mode()
                
                # Log ML decision
                shared_state["ml_decisions"].append({
                    "timestamp": datetime.now().isoformat(),
                    "anomaly_score": anomaly_score,
                    "decision": system_state.value,
                    "threshold_exceeded": anomaly_score > 0.7
                })
                
            update_shared_state()
            
    except Exception as e:
        print(f"Error in anomaly detection: {e}")

async def state_manager():
    """Background task to manage state transitions"""
    global system_state, safe_mode_timer
    
    while True:
        try:
            if system_state == SystemState.ATTACK_DETECTED and safe_mode_timer is not None:
                if safe_mode_timer > 0:
                    safe_mode_timer -= 1
                    
                    # Broadcast countdown update
                    await connection_manager.broadcast({
                        "type": "COUNTDOWN_UPDATE",
                        "countdown": safe_mode_timer
                    })
                    
                    if safe_mode_timer == 0:
                        # Countdown finished, trigger safe mode
                        await trigger_safe_mode()
            
            elif system_state == SystemState.ATTACK_SIMULATION and safe_mode_timer is not None:
                if safe_mode_timer > 0:
                    safe_mode_timer -= 1
                    
                    # Broadcast countdown update
                    await connection_manager.broadcast({
                        "type": "COUNTDOWN_UPDATE",
                        "countdown": safe_mode_timer
                    })
                    
                    if safe_mode_timer == 0:
                        # Countdown finished, trigger safe mode
                        await trigger_safe_mode()
                
            update_shared_state()
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error in state manager: {e}")
            await asyncio.sleep(1)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    
    # Send current state on connection
    await websocket.send_json({
        "type": "INITIAL_STATE",
        "state": system_state.value,
        "anomaly_score": anomaly_score,
        "ml_connected": shared_state["ml_connected"]
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "TELEMETRY":
                # Process telemetry data
                telemetry = data.get("data", [])
                
                # Run ML inference
                await detect_anomaly(telemetry)
                
                # Echo back with current state
                await websocket.send_json({
                    "type": "TELEMETRY_ACK",
                    "state": system_state.value,
                    "anomaly_score": anomaly_score,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif data.get("type") == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "state": system_state.value,
                    "ml_connected": shared_state["ml_connected"]
                })
                
            elif data.get("type") == "CONNECTION":
                await websocket.send_json({
                    "type": "CONNECTION_ACK",
                    "status": "CONNECTED",
                    "ml_model_ready": ml_model is not None
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@app.post("/api/simulate-attack", response_model=AttackResponse)
async def simulate_attack(attack_request: AttackRequest):
    """Endpoint to manually trigger attack simulation with 6-second countdown"""
    global system_state, safe_mode_timer
    
    if system_state == SystemState.SAFE_MODE:
        return JSONResponse({
            "status": "error",
            "message": "Already in safe mode. Refresh page to exit."
        })
    
    attack_type = attack_request.attack_type
    
    print(f"Simulating {attack_type} attack...")
    
    # Get anomaly score from ML model
    await simulate_attack_with_ml(attack_type)
    
    # Start attack simulation with 6-second countdown
    if await start_attack_simulation(attack_type):
        return JSONResponse({
            "status": "success",
            "message": f"{attack_type} attack simulation started. Switching to safe mode in 6 seconds",
            "anomaly_score": anomaly_score,
            "countdown": 6,
            "state": system_state.value
        })
    else:
        return JSONResponse({
            "status": "error",
            "message": "Failed to start attack simulation",
            "anomaly_score": 0.0,
            "state": system_state.value
        })

@app.post("/api/emergency-attack", response_model=AttackResponse)
async def emergency_attack():
    """Endpoint for immediate emergency attack (no countdown)"""
    global system_state
    
    if system_state == SystemState.SAFE_MODE:
        return JSONResponse({
            "status": "error",
            "message": "Already in safe mode. Refresh page to exit."
        })
    
    print("EMERGENCY ATTACK triggered!")
    
    # Get anomaly score from ML model
    await simulate_attack_with_ml("emergency")
    
    # Log emergency attack
    attack_timeline.append({
        "event": "EMERGENCY_ATTACK",
        "timestamp": datetime.now().isoformat(),
        "trigger": "MANUAL_EMERGENCY",
        "anomaly_score": anomaly_score
    })
    
    # Immediate safe mode
    await trigger_safe_mode()
    
    return JSONResponse({
        "status": "success",
        "message": "EMERGENCY ATTACK! Safe mode activated immediately.",
        "anomaly_score": anomaly_score,
        "countdown": 0,
        "state": system_state.value
    })

@app.post("/api/reset-system")
async def reset_system():
    """Reset system to normal state (admin only)"""
    global system_state, anomaly_score, safe_mode_timer, telemetry_buffer
    system_state = SystemState.NORMAL
    anomaly_score = 0.0
    safe_mode_timer = None
    telemetry_buffer = []
    
    update_shared_state()
    
    # Broadcast reset
    await connection_manager.broadcast({
        "type": "SYSTEM_RESET",
        "state": "NORMAL",
        "message": "System reset to normal mode"
    })
    
    return JSONResponse({
        "status": "success",
        "message": "System reset to NORMAL"
    })

@app.get("/api/system-state")
async def get_system_state():
    """Get current system state (for admin dashboard)"""
    return JSONResponse(shared_state)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "state": system_state.value,
        "ml_connected": shared_state["ml_connected"],
        "anomaly_score": anomaly_score,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/ml-status")
async def ml_status():
    """Get ML model status"""
    return {
        "ml_connected": ml_model is not None,
        "model_ready": ml_model is not None and ml_model.model is not None,
        "threshold": ml_model.threshold if ml_model else 0.0,
        "last_inference": shared_state["last_update"],
        "total_decisions": len(shared_state["ml_decisions"])
    }

if __name__ == "__main__":
    print("Starting Smart Scooter ML Backend...")
    print("Server will run on: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("\nAvailable endpoints:")
    print("  GET  /api/health        - Health check")
    print("  GET  /api/system-state  - Get current system state")
    print("  GET  /api/ml-status     - Get ML model status")
    print("  POST /api/simulate-attack - Simulate attack (6-second countdown)")
    print("  POST /api/emergency-attack - Emergency attack (immediate safe mode)")
    print("  POST /api/reset-system  - Reset system to normal")
    print("\nWebSocket: ws://localhost:8000/ws")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")