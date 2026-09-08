import { useEffect, useState } from "react";
import {
  Bluetooth,
  BrainCircuit,
  Play,
  ShieldCheck,
  ArrowUpRight,
} from "lucide-react";
import { api } from "./api";

type Status = {
  vehicles: number;
  sample_scans: number;
  ble_profiles: number;
  browser_ble_packets: number;
  model_runs: number;
};
export function BetaHub({
  token,
  onNavigate,
  onDemo,
  busy,
  canWrite,
}: {
  token: string;
  onNavigate: (path: string) => void;
  onDemo: () => void;
  busy: boolean;
  canWrite: boolean;
}) {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Status>("/beta/status", token)
      .then((data) => {
        if (active) setStatus(data);
      })
      .catch((reason) => {
        if (active) setError(reason.message);
      });
    return () => {
      active = false;
    };
  }, [token]);
  return (
    <section className="beta-hub">
      <div className="beta-hero">
        <h2>Inicio de Demo</h2>
        <button onClick={onDemo} disabled={busy || !canWrite} className="primary-button">
          <Play size={16} />
          {busy ? "Preparando…" : "Iniciar Demo"}
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="beta-cards">
        <article className="panel">
          <Bluetooth />
          <h3>Conexiones reales BLE</h3>
          <p>
            Selector de dispositivo y lectura GATT. Configura el mapa de bytes
            según el manual del manómetro.
          </p>
          <span className="badge warning">VALIDACIÓN DE CAMPO PENDIENTE</span>
          <button
            className="text-button"
            onClick={() => onNavigate("/connections")}
          >
            Abrir conexiones <ArrowUpRight size={15} />
          </button>
        </article>
        <article className="panel">
          <BrainCircuit />
          <h3>Laboratorio de modelos</h3>
          <p>
            Entrena una MLP o Random Forest. Ajusta parámetros, examina métricas
            SAMPLE y conserva experimentos.
          </p>
          <span className="badge">ENTRENAMIENTO REAL · DATOS SAMPLE</span>
          <button className="text-button" onClick={() => onNavigate("/models")}>
            Configurar modelos <ArrowUpRight size={15} />
          </button>
        </article>
        <article className="panel">
          <ShieldCheck />
          <h3>Calibración gobernada</h3>
          <p>
            La IA no escribe parámetros de carga. Sin una ficha OEM aprobada, el
            proceso sigue bloqueado.
          </p>
          <span className="badge warning">SOURCE_REQUIRED</span>
          <button
            className="text-button"
            onClick={() => onNavigate("/calibration")}
          >
            Ver requisitos <ArrowUpRight size={15} />
          </button>
        </article>
      </div>
      {status && (
        <div className="panel">
          <h2>Evidencia disponible en esta empresa</h2>
          <div className="beta-evidence">
            <span>
              <strong>{status.vehicles}</strong>equipos
            </span>
            <span>
              <strong>{status.sample_scans}</strong>sesiones SAMPLE
            </span>
            <span>
              <strong>{status.ble_profiles}</strong>mapas BLE configurados
            </span>
            <span>
              <strong>{status.browser_ble_packets}</strong>paquetes reportados
              por navegador
            </span>
            <span>
              <strong>{status.model_runs}</strong>experimentos
            </span>
          </div>
          <p className="muted">
            Los contadores proceden de la base de datos. Un paquete recibido por
            API no certifica por sí solo su origen físico. Todavía no hay
            validación OEM, ensayo de campo ni control de máquinas.
          </p>
        </div>
      )}
    </section>
  );
}
