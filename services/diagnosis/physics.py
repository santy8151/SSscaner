"""Measurement mathematics, with no OEM limits or actuator commands."""

from typing import Annotated, Literal

import numpy as np
from pydantic import Field, FiniteFloat
from scipy.signal import periodogram

from packages.shared.contracts import StrictModel


class SignalRequest(StrictModel):
    origin: Literal["MANUAL_IMPORT", "SAMPLE"]
    sample_rate_hz: FiniteFloat = Field(gt=0, le=10000000)
    samples: list[Annotated[FiniteFloat, Field(ge=-1e9, le=1e9)]] = Field(min_length=32, max_length=2048)


def analyze_signal(payload: SignalRequest):
    values = np.array(payload.samples)
    frequency, power = periodogram(values, fs=payload.sample_rate_hz, window="hann", detrend="constant")
    peak = int(np.argmax(power[1:]) + 1)
    return {
        "origin": payload.origin,
        "dominant_frequency_hz": float(frequency[peak]) if np.ptp(values) > 1e-12 else None,
        "resolution_hz": payload.sample_rate_hz / len(values),
        "nyquist_hz": payload.sample_rate_hz / 2,
        "rms": float(np.sqrt(np.mean(values**2))),
        "peak_to_peak": float(np.ptp(values)),
        "samples": len(values),
        "limitation": "Frecuencia dominante, no necesariamente fundamental. Muestreo uniforme y filtro antialias requeridos. Amplitud en unidades de entrada.",
    }


class ElectricalRequest(StrictModel):
    voltage_v: FiniteFloat = Field(ge=0, le=2000)
    current_a: FiniteFloat = Field(ge=-5000, le=5000)
    duration_seconds: FiniteFloat = Field(ge=0, le=86400)


def dc_energy(payload: ElectricalRequest):
    watts = payload.voltage_v * payload.current_a
    return {
        "origin": "MANUAL",
        "power_w": watts,
        "energy_wh": watts * payload.duration_seconds / 3600,
        "assumption": "DC constante durante el intervalo; no válido para AC/PWM ni potencia trifásica sin integrar v(t)i(t).",
    }


class PerformancePoint(StrictModel):
    torque_nm: FiniteFloat = Field(ge=0, le=20000)
    shaft_rpm: FiniteFloat = Field(ge=0, le=50000)
    voltage_v: FiniteFloat = Field(gt=0, le=2000)
    current_a: FiniteFloat = Field(gt=0, le=5000)
    speed_kmh: FiniteFloat = Field(ge=0, le=400)
    turn_radius_m: FiniteFloat = Field(gt=0, le=100000)


class PerformanceRequest(StrictModel):
    before: PerformancePoint
    after: PerformancePoint
    conditions: str = Field(min_length=15, max_length=1000)


def compare_performance(payload: PerformanceRequest):
    def point(item):
        mechanical = item.torque_nm * item.shaft_rpm * 2 * np.pi / 60
        electrical = item.voltage_v * item.current_a
        consistent = mechanical <= electrical
        return {
            "shaft_power_kw": mechanical / 1000,
            "dc_input_kw": electrical / 1000,
            "apparent_efficiency": mechanical / electrical if consistent else None,
            "steady_turn_acceleration_ms2": (item.speed_kmh / 3.6) ** 2 / item.turn_radius_m,
            "energy_balance_consistent": consistent,
        }

    before, after = point(payload.before), point(payload.after)
    return {
        "origin": "MANUAL",
        "before": before,
        "after": after,
        "delta_shaft_power_kw": after["shaft_power_kw"] - before["shaft_power_kw"],
        "conditions": payload.conditions,
        "grip_improvement": None,
        "ecu_commands": False,
        "limitation": "Potencia en régimen estacionario de motorización DC, mediciones simultáneas en la misma frontera energética. v²/R estima aceleración en giro circular, no agarre disponible. Comparación descriptiva: no demuestra causalidad ni autoriza modificaciones.",
    }
