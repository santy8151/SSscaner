from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import numpy as np
import json
import logging
import os
from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import tensorflow as tf
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import redis
import pickle
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-service")

app = FastAPI(title="SSSCANER ML Service", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ml.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

redis_client = redis.from_url(REDIS_URL, decode_responses=False)

class NodeType(str, Enum):
    COMPRESSOR = "compressor"
    EVAPORATOR = "evaporator"
    CONDENSER = "condenser"
    CHILLER = "chiller"
    AC_MOTOR = "ac_motor"

class Algorithm(str, Enum):
    DECISION_TREE = "decision_tree"
    LINEAR_REGRESSION = "linear_regression"
    BAYESIAN_NETWORK = "bayesian_network"
    MLP_NEURAL_NETWORK = "mlp_neural_network"

class NeuralNode(Base):
    __tablename__ = "neural_nodes"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    node_type = Column(String)
    algorithm = Column(String)
    is_trained = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    epochs = Column(Integer, default=50)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"
    
    id = Column(String, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    node_id = Column(String, index=True)
    fault_detected = Column(Integer, default=0)
    fault_code = Column(String, nullable=True)
    severity = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sensor_readings = Column(JSON)
    recommendations = Column(JSON)
    ai_explanation = Column(String)

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    vehicle_type = Column(String)
    vin = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class TensorFlowModelManager:
    def __init__(self):
        self.models: Dict[str, tf.keras.Model] = {}
        self.pca_models: Dict[str, PCA] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self._load_cached_models()
    
    def _load_cached_models(self):
        logger.info("Loading cached models...")
        for key in redis_client.keys("model:*"):
            try:
                model_data = redis_client.get(key)
                if model_data:
                    logger.info(f"Loaded cached model {key}")
            except Exception as e:
                logger.error(f"Failed to load cached model {key}: {e}")
    
    async def predict(self, node_id: str, input_data: Dict[str, float]) -> Dict[str, Any]:
        if node_id not in self.models:
            raise ValueError(f"Model {node_id} not trained")
        
        model = self.models[node_id]
        features = [input_data.get(f, 0.0) for f in ["pressure_suction", "pressure_discharge", "temperature_evaporator", "temperature_condenser", "voltage", "current"]]
        input_array = np.array([features])
        
        if node_id in self.scalers:
            input_array = self.scalers[node_id].transform(input_array)
        
        if node_id in self.pca_models:
            input_array = self.pca_models[node_id].transform(input_array)
        
        prediction = model.predict(input_array, verbose=0)
        score = float(prediction[0][0])
        
        fault_detected = score > 0.5
        severity = min(max(score, 0.0), 1.0)
        
        return {
            "fault_detected": fault_detected,
            "severity": severity,
            "confidence": score,
            "prediction": float(score)
        }
    
    async def train(self, node_id: str, training_data: Dict[str, Any], algorithm: str = "mlp") -> Dict[str, Any]:
        X_train = np.array(training_data['X_train'])
        y_train = np.array(training_data['y_train'])
        X_val = np.array(training_data['X_val'])
        y_val = np.array(training_data['y_val'])
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        self.scalers[node_id] = scaler
        
        n_components = min(20, X_train_scaled.shape[1])
        pca = PCA(n_components=n_components)
        X_train_pca = pca.fit_transform(X_train_scaled)
        X_val_pca = pca.transform(X_val_scaled)
        self.pca_models[node_id] = pca
        
        if algorithm == "linear_regression":
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(X_train_pca.shape[1],)),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
        else:
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(X_train_pca.shape[1],)),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        
        history = model.fit(
            X_train_pca, y_train,
            validation_data=(X_val_pca, y_val),
            epochs=training_data.get('epochs', 50),
            batch_size=training_data.get('batch_size', 32),
            verbose=0
        )
        
        self.models[node_id] = model
        
        max_val_accuracy = float(max(history.history['val_accuracy']))
        logger.info(f"Model {node_id} trained with accuracy {max_val_accuracy:.4f}")
        
        try:
            model_bytes = pickle.dumps(model)
            redis_client.set(f"model:{node_id}", model_bytes, ex=604800)
        except Exception as e:
            logger.warning(f"Could not cache model: {e}")
        
        return {
            "accuracy": max_val_accuracy,
            "loss": float(min(history.history['val_loss'])),
            "epochs": len(history.history['val_accuracy'])
        }
    
    def get_recommendations(self, node_type: str, fault: bool) -> List[str]:
        if not fault:
            return ["Sistema funcionando correctamente"]
        
        recs = {
            "compressor": ["Revisar presión succión", "Verificar refrigerante", "Inspeccionar válvula de control"],
            "evaporator": ["Limpiar serpentín", "Revisar flujo aire", "Verificar bloqueo de hielo"],
            "condenser": ["Limpiar condensador", "Verificar ventilador", "Revisar presión de descarga"],
            "chiller": ["Revisar termostato", "Verificar bomba", "Inspeccionar tuberías"],
            "ac_motor": ["Medir voltaje", "Revisar conexiones", "Inspeccionar bobinado"]
        }
        return recs.get(node_type, ["Consultar manual técnico"])

ml_manager = TensorFlowModelManager()

class TrainRequest(BaseModel):
    epochs: int = 50
    algorithm: str = "mlp"
    batch_size: int = 32

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_synthetic_training_data(n_samples=1000):
    np.random.seed(42)
    normal = {
        'pressure_suction': np.random.normal(30, 5, n_samples // 2),
        'pressure_discharge': np.random.normal(250, 20, n_samples // 2),
        'temperature_evaporator': np.random.normal(5, 2, n_samples // 2),
        'temperature_condenser': np.random.normal(45, 5, n_samples // 2),
        'voltage': np.random.normal(12, 0.5, n_samples // 2),
        'current': np.random.normal(5, 1, n_samples // 2),
        'fault': np.zeros(n_samples // 2)
    }
    fault = {
        'pressure_suction': np.random.normal(15, 8, n_samples // 2),
        'pressure_discharge': np.random.normal(300, 30, n_samples // 2),
        'temperature_evaporator': np.random.normal(15, 5, n_samples // 2),
        'temperature_condenser': np.random.normal(60, 10, n_samples // 2),
        'voltage': np.random.normal(10, 2, n_samples // 2),
        'current': np.random.normal(8, 2, n_samples // 2),
        'fault': np.ones(n_samples // 2)
    }
    
    data = {k: np.concatenate([normal[k], fault[k]]) for k in normal.keys()}
    
    indices = np.random.permutation(len(data['pressure_suction']))
    for key in data:
        data[key] = data[key][indices]
    
    split = int(0.8 * len(data['pressure_suction']))
    
    X_train = np.column_stack([data[k][:split] for k in ['pressure_suction', 'pressure_discharge', 'temperature_evaporator', 'temperature_condenser', 'voltage', 'current']])
    y_train = data['fault'][:split]
    X_val = np.column_stack([data[k][split:] for k in ['pressure_suction', 'pressure_discharge', 'temperature_evaporator', 'temperature_condenser', 'voltage', 'current']])
    y_val = data['fault'][split:]
    
    return {"X_train": X_train, "y_train": y_train, "X_val": X_val, "y_val": y_val}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml-service"}

@app.get("/api/v1/nodes")
async def get_nodes(db: Session = Depends(get_db)):
    nodes = db.query(NeuralNode).all()
    return {
        "total": len(nodes),
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "type": node.node_type,
                "algorithm": node.algorithm,
                "trained": bool(node.is_trained),
                "accuracy": node.accuracy,
                "epochs": node.epochs
            }
            for node in nodes
        ]
    }

@app.post("/api/v1/diagnose")
async def diagnose(vehicle_id: str, measurements: Dict[str, Any], db: Session = Depends(get_db)):
    nodes = db.query(NeuralNode).all()
    diagnostics = []
    critical_count = 0
    
    for node in nodes:
        if node.is_trained:
            try:
                result = await ml_manager.predict(node.id, measurements)
                
                diag = DiagnosticResult(
                    id=f"diag_{datetime.utcnow().timestamp()}",
                    vehicle_id=vehicle_id,
                    node_id=node.id,
                    fault_detected=int(result['fault_detected']),
                    fault_code=f"FAULT_{node.node_type.upper()}" if result['fault_detected'] else None,
                    severity=result['severity'],
                    confidence=result['confidence'],
                    sensor_readings=measurements,
                    recommendations=ml_manager.get_recommendations(node.node_type, result['fault_detected'])
                )
                
                if result['severity'] > 0.7:
                    critical_count += 1
                
                db.add(diag)
                diagnostics.append({
                    "node_id": node.id,
                    "fault_detected": result['fault_detected'],
                    "severity": result['severity'],
                    "confidence": result['confidence'],
                    "recommendations": diag.recommendations
                })
            except Exception as e:
                logger.error(f"Error diagnosing node {node.id}: {e}")
    
    db.commit()
    
    return {
        "vehicle_id": vehicle_id,
        "diagnostics": diagnostics,
        "critical_count": critical_count,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/nodes/{node_id}/train")
async def train_node(
    node_id: str,
    request: TrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    node = db.query(NeuralNode).filter(NeuralNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    training_data = generate_synthetic_training_data()
    training_data['epochs'] = request.epochs
    training_data['batch_size'] = request.batch_size
    
    result = await ml_manager.train(node_id, training_data, request.algorithm)
    
    node.is_trained = 1
    node.accuracy = result['accuracy']
    node.epochs = request.epochs
    node.algorithm = request.algorithm
    node.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Node {node_id} trained with accuracy {result['accuracy']:.4f}")
    
    return {
        "node_id": node_id,
        "status": "trained",
        "accuracy": result['accuracy'],
        "epochs": result['epochs']
    }

@app.get("/api/v1/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return {
        "id": vehicle.id,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "type": vehicle.vehicle_type,
        "vin": vehicle.vin
    }

@app.post("/api/v1/vehicles")
async def create_vehicle(
    make: str,
    model: str,
    year: int,
    vehicle_type: str,
    vin: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    vehicle = Vehicle(
        id=f"vh_{datetime.utcnow().timestamp()}",
        user_id=user_id,
        make=make,
        model=model,
        year=year,
        vehicle_type=vehicle_type,
        vin=vin
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    
    logger.info(f"Vehicle created: {vehicle.id}")
    
    return {
        "id": vehicle.id,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year
    }

@app.get("/api/v1/diagnostics/history/{vehicle_id}")
async def get_diagnostics_history(vehicle_id: str, limit: int = 20, db: Session = Depends(get_db)):
    diagnostics = db.query(DiagnosticResult).filter(
        DiagnosticResult.vehicle_id == vehicle_id
    ).order_by(DiagnosticResult.timestamp.desc()).limit(limit).all()
    
    return {
        "total": len(diagnostics),
        "diagnostics": [
            {
                "id": d.id,
                "node_id": d.node_id,
                "timestamp": d.timestamp,
                "fault_detected": bool(d.fault_detected),
                "severity": d.severity,
                "confidence": d.confidence,
                "recommendations": d.recommendations
            }
            for d in diagnostics
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
