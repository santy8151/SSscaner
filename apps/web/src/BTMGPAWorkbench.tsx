import { useState, type FormEvent } from "react";
import { api, downloadJSON } from "./api";
type Point = {
  shaft_power_kw: number;
  dc_input_kw: number;
  apparent_efficiency: number | null;
  steady_turn_acceleration_ms2: number;
  energy_balance_consistent: boolean;
};
type Result = {
  before: Point;
  after: Point;
  delta_shaft_power_kw: number;
  limitation: string;
};
const fields = [
  ["torque_nm", "Par en eje (N·m)", 0, 20000],
  ["shaft_rpm", "Velocidad del eje (rpm)", 0, 50000],
  ["voltage_v", "Tensión DC (V)", 0.001, 2000],
  ["current_a", "Corriente DC (A)", 0.001, 5000],
  ["speed_kmh", "Velocidad del vehículo (km/h)", 0, 400],
  ["turn_radius_m", "Radio de giro (m)", 0.001, 100000],
] as const;
export function BTMGPAWorkbench({ token }: { token: string }) {
  const [result, setResult] = useState<Result | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [evidence, setEvidence] = useState<unknown>(null);
  async function compare(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setResult(null);
    setBusy(true);
    setError("");
    const f = new FormData(e.currentTarget);
    const point = (prefix: string) =>
      Object.fromEntries(
        fields.map(([key]) => [key, Number(f.get(prefix + key))]),
      );
    const payload = {
      before: point("before_"),
      after: point("after_"),
      conditions: f.get("conditions"),
    };
    try {
      const data = await api<Result>("/physics/performance", token, payload);
      setResult(data);
      setEvidence({
        input: payload,
        result: data,
        recorded_at: new Date().toISOString(),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel btmgpa-workbench">
      <p className="eyebrow">BTMGPA / BANCO MODULAR</p>
      <h2>De equipo de servicio a banco de diagnóstico</h2>
      <p>
        Concepto de adaptación descrito por el fundador: una base de limpieza
        del sistema de refrigeración, ampliada con adquisición de señales,
        osciloscopio y visión. La adaptación física requiere documentar equipo,
        circuito y compatibilidad.
      </p>
      <div className="component-buttons">
        <span className="badge">Base de servicio · adaptación por validar</span>
        <span className="badge">Salva memorias · alimentación</span>
        <span className="badge">Adaptador de datos · protocolo requerido</span>
      </div>
      <div className="btmgpa-flow">
        <div>
          <b>01 · Presión y temperatura</b>
          <small>Circuito refrigerante y chiller</small>
        </div>
        <span>→</span>
        <div>
          <b>02 · Señal eléctrica</b>
          <small>Osciloscopio, tensión y frecuencia</small>
        </div>
        <span>→</span>
        <div>
          <b>03 · Visión de luces</b>
          <small>Faros y carrocería; no continuidad eléctrica</small>
        </div>
      </div>
      <p className="muted">
        El salva memorias mantiene alimentación: la ruta de datos necesita un
        escáner o adaptador independiente. Las tres vistas permanecen dentro de
        Instrumentos. El circuito de líquido refrigerante y el de refrigerante
        A/C no son intercambiables.
      </p>
      <details>
        <summary>
          Comparar mediciones de motor y dinámica: antes / después
        </summary>
        <p>
          Registra mediciones de un ensayo controlado. Se calcula potencia
          mecánica, balance DC y aceleración lateral ideal. Para evaluar agarre
          hacen falta neumáticos, superficie, carga, ángulo de dirección,
          guiñada, deslizamiento y repetición del ensayo. No hay un ajuste
          automático de motor o estabilidad.
        </p>
        <form
          onSubmit={compare}
          onChange={() => {
            setResult(null);
            setEvidence(null);
          }}
        >
          <div className="comparison-grid">
            {["before", "after"].map((prefix, i) => (
              <fieldset key={prefix}>
                <legend>{i ? "Después" : "Antes"}</legend>
                {fields.map(([key, label, min, max]) => (
                  <label key={key}>
                    {label}
                    <input
                      aria-label={`${i ? "Después" : "Antes"}: ${label}`}
                      required
                      type="number"
                      step="any"
                      name={prefix + "_" + key}
                      min={min}
                      max={max}
                    />
                  </label>
                ))}
              </fieldset>
            ))}
          </div>
          <label>
            Condiciones y procedencia de las mediciones
            <textarea
              name="conditions"
              minLength={15}
              maxLength={1000}
              required
              placeholder="Vehículo, fecha, equipo, estado de carga, temperaturas, neumáticos, superficie y condiciones del ensayo"
            />
          </label>
          <button disabled={busy}>
            {busy ? "Calculando…" : "Comparar mediciones"}
          </button>
        </form>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {result && (
          <>
            <div className="comparison-grid">
              {[result.before, result.after].map((p, i) => (
                <div className="panel" key={i}>
                  <h3>{i ? "Después" : "Antes"}</h3>
                  <p>
                    Potencia en eje: <b>{p.shaft_power_kw.toFixed(2)} kW</b>
                  </p>
                  <p>Entrada DC: {p.dc_input_kw.toFixed(2)} kW</p>
                  <p>
                    Eficiencia aparente:{" "}
                    {p.apparent_efficiency === null
                      ? "No calculable: revisar balance energético"
                      : (p.apparent_efficiency * 100).toFixed(1) + "%"}
                  </p>
                  <p>
                    Aceleración lateral ideal:{" "}
                    {p.steady_turn_acceleration_ms2.toFixed(2)} m/s²
                  </p>
                </div>
              ))}
            </div>
            <p>
              Diferencia de potencia en eje:{" "}
              {result.delta_shaft_power_kw.toFixed(2)} kW. La diferencia no
              demuestra una mejora de agarre.
            </p>
            <p className="muted">{result.limitation}</p>
            <button
              className="ghost"
              onClick={() =>
                downloadJSON(evidence, "SSScanner-ensayo-comparativo.json")
              }
            >
              Exportar evidencia comparativa
            </button>
          </>
        )}
      </details>
    </section>
  );
}
