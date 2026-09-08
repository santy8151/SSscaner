"""Real training on synthetic fixtures. No vehicle diagnosis or calibration authority."""

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Literal

import joblib
import numpy as np
from pydantic import Field, FiniteFloat, model_validator
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from apps.api.database import ModelRun
from hardware.simulator.vehicle import SCENARIOS, VehicleSimulator
from packages.shared.contracts import StrictModel


class MLPConfiguration(StrictModel):
    model: Literal["mlp"]
    hidden_layers: list[Annotated[int, Field(ge=4, le=128)]] = Field(
        default_factory=lambda: [64, 32], min_length=1, max_length=3
    )
    activation: Literal["relu", "tanh", "logistic"] = "relu"
    optimizer: Literal["adam", "sgd"] = "adam"
    epochs: int = Field(default=60, ge=1, le=300)
    batch_size: int = Field(default=32, ge=8, le=256)
    learning_rate: FiniteFloat = Field(default=0.001, ge=0.00001, le=0.1)


class ForestConfiguration(StrictModel):
    model: Literal["random_forest"]
    trees: int = Field(default=80, ge=10, le=200)
    max_depth: int = Field(default=8, ge=2, le=30)


class KMeansConfiguration(StrictModel):
    model: Literal["kmeans"]
    clusters: int = Field(default=4, ge=2, le=12)
    iterations: int = Field(default=100, ge=10, le=300)


class PCAConfiguration(StrictModel):
    model: Literal["pca"]
    components: int = Field(default=2, ge=1, le=3)


class IsolationConfiguration(StrictModel):
    model: Literal["isolation_forest"]
    trees: int = Field(default=80, ge=10, le=200)
    contamination: FiniteFloat = Field(default=0.05, ge=0.001, le=0.3)


class TrainingRequest(StrictModel):
    dataset_origin: Literal["SAMPLE"]
    configuration: Annotated[
        MLPConfiguration | ForestConfiguration | KMeansConfiguration | PCAConfiguration | IsolationConfiguration,
        Field(discriminator="model"),
    ]
    component: Literal["system", "compressor", "condenser", "evaporator", "motor"] = "system"
    samples_per_class: int = Field(default=60, ge=25, le=150)
    seed: int = Field(default=42, ge=0, le=2147483647)

    @model_validator(mode="after")
    def batch_fits(self):
        train_count = int(self.samples_per_class * 7 * 0.75)
        if isinstance(self.configuration, MLPConfiguration) and self.configuration.batch_size > train_count:
            raise ValueError("Batch size supera el número de muestras de entrenamiento")
        return self


FEATURES = [
    "rpm",
    "engine_temperature",
    "voltage",
    "low_pressure",
    "high_pressure",
    "ambient_temperature",
    "evaporator_temperature",
    "compressor_on",
    "fan_on",
]


def dataset(samples_per_class: int, seed: int):
    rng = np.random.default_rng(seed)
    x, y = [], []
    for scenario in SCENARIOS:
        if scenario == "disconnected":
            continue
        simulator = VehicleSimulator(scenario)
        for index in range(samples_per_class):
            values = {reading.signal: reading.value for reading in simulator.read_sample(index).readings}
            row = []
            for signal in FEATURES:
                value = values[signal]
                row.append(
                    np.nan
                    if value is None
                    else value
                    if signal.endswith("_on")
                    else value + rng.normal(0, max(0.1, abs(value) * 0.025))
                )
            x.append(row)
            y.append(scenario)
    return np.array(x, dtype=float), np.array(y)


def train_sample(request: TrainingRequest, progress, artifact_path: Path) -> dict:
    x, y = dataset(request.samples_per_class, request.seed)
    component_features = {
        "compressor": ["low_pressure", "high_pressure", "voltage", "compressor_on"],
        "condenser": ["high_pressure", "ambient_temperature", "fan_on"],
        "evaporator": ["low_pressure", "evaporator_temperature", "ambient_temperature"],
        "motor": ["rpm", "engine_temperature", "voltage"],
    }
    features = component_features.get(request.component, FEATURES)
    x = x[:, [FEATURES.index(name) for name in features]]
    digest = hashlib.sha256(x.tobytes() + "|".join(y).encode()).hexdigest()
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=request.seed, stratify=y)
    imputer = SimpleImputer(add_indicator=True)
    scaler = StandardScaler()
    train = scaler.fit_transform(imputer.fit_transform(x_train))
    test = scaler.transform(imputer.transform(x_test))
    config = request.configuration
    loss = []
    metrics = {}
    with threadpool_limits(limits=1):
        if isinstance(config, MLPConfiguration):
            model = MLPClassifier(
                hidden_layer_sizes=tuple(config.hidden_layers),
                activation=config.activation,
                solver=config.optimizer,
                batch_size=config.batch_size,
                learning_rate_init=config.learning_rate,
                max_iter=1,
                random_state=request.seed,
            )
            for epoch in range(config.epochs):
                model.partial_fit(train, y_train, classes=np.unique(y))
                loss.append(float(model.loss_))
                if not np.isfinite(model.loss_):
                    raise ValueError("Entrenamiento divergente; reduce learning rate")
                if epoch % max(1, config.epochs // 20) == 0:
                    progress(min(95, int((epoch + 1) / config.epochs * 95)))
        elif isinstance(config, ForestConfiguration):
            progress(10)
            model = RandomForestClassifier(
                n_estimators=config.trees, max_depth=config.max_depth, n_jobs=1, random_state=request.seed
            )
            model.fit(train, y_train)
            progress(90)
        elif isinstance(config, KMeansConfiguration):
            model = KMeans(n_clusters=config.clusters, max_iter=config.iterations, n_init=10, random_state=request.seed)
            model.fit(train)
            metrics = {
                "test_cluster_counts": np.bincount(model.predict(test), minlength=config.clusters).tolist(),
                "train_inertia": float(model.inertia_),
            }
        elif isinstance(config, PCAConfiguration):
            model = PCA(n_components=config.components, svd_solver="full")
            model.fit(train)
            reconstructed = model.inverse_transform(model.transform(test))
            metrics = {
                "explained_variance_ratio": model.explained_variance_ratio_.tolist(),
                "test_reconstruction_mse": float(np.mean((test - reconstructed) ** 2)),
            }
        else:
            model = IsolationForest(
                n_estimators=config.trees, contamination=config.contamination, random_state=request.seed, n_jobs=1
            )
            model.fit(train)
            metrics = {"test_outlier_fraction": float(np.mean(model.predict(test) == -1))}
        if isinstance(config, (MLPConfiguration, ForestConfiguration)):
            prediction = model.predict(test)
            labels = list(model.classes_)
            metrics = {
                "accuracy_sample": float(accuracy_score(y_test, prediction)),
                "f1_macro_sample": float(f1_score(y_test, prediction, average="macro", zero_division=0)),
                "labels": labels,
                "confusion_matrix": confusion_matrix(y_test, prediction, labels=labels).tolist(),
            }
        progress(95)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = artifact_path.with_suffix(".tmp")
    joblib.dump(
        {
            "model": model,
            "imputer": imputer,
            "scaler": scaler,
            "features": features,
            "origin": "SAMPLE",
            "configuration": request.model_dump(),
            "dataset_hash": digest,
        },
        temporary,
    )
    temporary.replace(artifact_path)
    return {
        "dataset_origin": "SAMPLE",
        "dataset_version": "synthetic-fixtures-v1",
        "dataset_hash": digest,
        "training_samples": len(train),
        "test_samples": len(test),
        **metrics,
        "features": features,
        "component": request.component,
        "loss_curve": loss,
        "epochs_completed": len(loss),
        "artifact_saved": True,
        "valid_for_real_diagnosis": False,
        "calibration_authority": False,
        "limitation": "Métricas sobre fixtures sintéticos con ruido. No miden rendimiento en vehículos reales ni probabilidad de avería.",
    }


class TrainingRunner:
    """Single bounded local worker. No model upload or untrusted pickle loading."""

    def __init__(self, session_factory, artifact_dir: Path):
        self.sessions = session_factory
        self.artifact_dir = artifact_dir
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ssscanner-sample-ml")
        self.slot = threading.BoundedSemaphore(1)

    def reserve(self) -> bool:
        return self.slot.acquire(blocking=False)

    def start(self, run_id: str):
        try:
            self.executor.submit(self._work, run_id)
        except Exception:
            self.slot.release()
            raise

    def _work(self, run_id):
        try:
            with self.sessions.begin() as db:
                row = db.get(ModelRun, run_id)
                config = TrainingRequest.model_validate(row.configuration)
                organization_id = row.organization_id
                row.status = "running"

            def progress(percent):
                with self.sessions.begin() as db:
                    db.get(ModelRun, run_id).progress = percent

            result = train_sample(config, progress, self.artifact_dir / organization_id / f"{run_id}.joblib")
            with self.sessions.begin() as db:
                row = db.get(ModelRun, run_id)
                row.status = "completed"
                row.progress = 100
                row.result = result
        except Exception:
            with self.sessions.begin() as db:
                row = db.get(ModelRun, run_id)
                if row:
                    row.status = "failed"
                    row.result = {
                        "error": "Entrenamiento interrumpido o configuración inestable. Revisa recursos y parámetros.",
                        "valid_for_real_diagnosis": False,
                    }
        finally:
            self.slot.release()

    def shutdown(self):
        self.executor.shutdown(wait=True)
