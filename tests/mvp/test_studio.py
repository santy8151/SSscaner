import joblib
import numpy as np
import pytest
from pydantic import ValidationError

from services.diagnosis.physics import ElectricalRequest, SignalRequest, analyze_signal, dc_energy
from services.ml.lab import TrainingRequest, train_sample
from tests.mvp.test_api import register
from tests.mvp.test_beta import client  # noqa: F401


@pytest.mark.parametrize(
    "config,metric",
    [
        ({"model": "kmeans", "clusters": 3, "iterations": 30}, "test_cluster_counts"),
        ({"model": "pca", "components": 2}, "explained_variance_ratio"),
        ({"model": "isolation_forest", "trees": 10, "contamination": 0.05}, "test_outlier_fraction"),
    ],
)
def test_unsupervised_models_do_not_report_diagnostic_accuracy(tmp_path, config, metric):
    path = tmp_path / "model.joblib"
    result = train_sample(
        TrainingRequest(dataset_origin="SAMPLE", component="compressor", configuration=config, samples_per_class=25),
        lambda _: None,
        path,
    )
    assert metric in result and "accuracy_sample" not in result
    assert result["valid_for_real_diagnosis"] is False
    artifact = joblib.load(path)
    assert artifact["features"] == ["low_pressure", "high_pressure", "voltage", "compressor_on"]
    assert artifact["model"].n_features_in_ == artifact["scaler"].n_features_in_


def test_signal_math_and_dc_energy():
    samples = (2 * np.sin(2 * np.pi * 62.5 * np.arange(256) / 1000)).tolist()
    result = analyze_signal(SignalRequest(origin="SAMPLE", sample_rate_hz=1000, samples=samples))
    assert result["dominant_frequency_hz"] == 62.5
    assert result["rms"] == pytest.approx(2**0.5)
    assert (
        analyze_signal(SignalRequest(origin="MANUAL_IMPORT", sample_rate_hz=1000, samples=[12] * 32))[
            "dominant_frequency_hz"
        ]
        is None
    )
    assert dc_energy(ElectricalRequest(voltage_v=12, current_a=2, duration_seconds=3600))["energy_wh"] == 24
    with pytest.raises(ValidationError):
        SignalRequest(origin="SAMPLE", sample_rate_hz=1000, samples=[1e300] * 32)
    with pytest.raises(ValidationError):
        TrainingRequest(dataset_origin="SAMPLE", configuration={"model": "pca", "learning_rate": 0.01})


def test_beta_routes_and_physics_auth(client):  # noqa: F811
    for path in ["dashboard", "calibration", "beta", "connections", "settings", "vehicles"]:
        assert client.get("/" + path).status_code == 404
    for path in ["instruments", "models"]:
        assert client.get("/" + path).status_code == 200
    payload = {"origin": "SAMPLE", "sample_rate_hz": 1000, "samples": [0] * 32}
    assert client.post("/api/v1/physics/frequency", json=payload).status_code == 401
    headers = register(client)
    assert (
        client.post("/api/v1/physics/frequency", headers=headers, json=payload).json()["dominant_frequency_hz"] is None
    )
