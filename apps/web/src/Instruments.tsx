import { useEffect, useState, type FormEvent } from "react";
import { api, downloadJSON } from "./api";
import { BleConnections } from "./BleConnections";
import { BTMGPAWorkbench } from "./BTMGPAWorkbench";
type Vehicle = { id: string; name: string };
type Reading = {
  signal: string;
  value: number | null;
  unit: string;
  observed_at?: string;
};
type Profile = { id: string; vehicle_id: string };
type Scan = {
  id: string;
  batches: { origin: string; observed_at: string; readings: Reading[] }[];
};
type Spectrum = {
  dominant_frequency_hz: number | null;
  resolution_hz: number;
  rms: number;
  peak_to_peak: number;
  limitation: string;
  origin: string;
};
export function Instruments({
  token,
  canWrite,
}: {
  token: string;
  canWrite: boolean;
}) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]),
    [vehicle, setVehicle] = useState(""),
    [readings, setReadings] = useState<Reading[]>([]),
    [origin, setOrigin] = useState("SIN LECTURAS"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [ble, setBle] = useState(false),
    [signal, setSignal] = useState(""),
    [rate, setRate] = useState(1000),
    [spectrum, setSpectrum] = useState<Spectrum | null>(null),
    [energy, setEnergy] = useState<unknown>(null),
    [source, setSource] = useState<"MANUAL_IMPORT" | "SAMPLE">("MANUAL_IMPORT");
  useEffect(() => {
    let live = true;
    api<Vehicle[]>("/vehicles", token)
      .then((v) => {
        if (live) {
          setVehicles(v);
          setVehicle(v[0]?.id || "");
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [token]);
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await work();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = String(new FormData(e.currentTarget).get("name"));
    await action(async () => {
      const v = await api<Vehicle>("/vehicles", token, { name, kind: "light" });
      setVehicles((old) => [v, ...old]);
      setVehicle(v.id);
      setReadings([]);
      setOrigin("SIN LECTURAS");
    });
  }
  async function sample() {
    await action(async () => {
      let selected = vehicle;
      if (!selected) {
        const v = await api<Vehicle>("/vehicles", token, {
          name: "Banco de demostración SAMPLE",
          kind: "light",
        });
        setVehicles((old) => [v, ...old]);
        setVehicle(v.id);
        selected = v.id;
      }
      const scan = await api<Scan>("/simulator/scans", token, {
        vehicle_id: selected,
        scenario: "normal",
        protocol: "EXTERNAL",
      });
      const batch = scan.batches.at(-1)!;
      setReadings(
        batch.readings.map((r) => ({ ...r, observed_at: batch.observed_at })),
      );
      setOrigin("SAMPLE · Captura guardada");
    });
  }
  async function readBle() {
    await action(async () => {
      const profiles = (await api<Profile[]>("/devices", token)).filter(
        (p) => p.vehicle_id === vehicle,
      );
      const batches = await Promise.all(
        profiles.map((p) => api<Reading[]>(`/devices/${p.id}/readings`, token)),
      );
      setReadings(
        batches
          .flatMap((rows) => rows.slice(0, 1))
          .sort((a, b) =>
            (b.observed_at || "").localeCompare(a.observed_at || ""),
          ),
      );
      setOrigin("CLIENT_BLE · Últimas lecturas guardadas; mapeo sin validar");
    });
  }
  async function analyze() {
    await action(async () => {
      const samples = signal
        .trim()
        .split(/[\s,;]+/)
        .map(Number);
      setSpectrum(
        await api<Spectrum>("/physics/frequency", token, {
          origin: source,
          sample_rate_hz: rate,
          samples,
        }),
      );
    });
  }
  function sampleWave() {
    setRate(1000);
    setSignal(
      Array.from({ length: 256 }, (_, i) =>
        (2 * Math.sin((2 * Math.PI * 62.5 * i) / 1000)).toFixed(6),
      ).join(", "),
    );
    setSource("SAMPLE");
    setSpectrum(null);
  }
  const low = readings.find((r) => r.signal === "low_pressure"),
    high = readings.find((r) => r.signal === "high_pressure");
  return (
    <>
      <section className="panel">
        <div className="instrument-toolbar">
          <label>
            Vehículo / banco
            <select
              value={vehicle}
              onChange={(e) => {
                setVehicle(e.target.value);
                setReadings([]);
                setOrigin("SIN LECTURAS");
              }}
            >
              <option value="">Selecciona</option>
              {vehicles.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </label>
          <button disabled={busy || !canWrite} onClick={sample}>
            Cargar demo SAMPLE
          </button>
          <button
            className="ghost"
            disabled={busy || !vehicle}
            onClick={readBle}
          >
            Actualizar lecturas BLE
          </button>
          <button className="ghost" onClick={() => setBle(!ble)}>
            {ble ? "Cerrar conexiones" : "Conectar sensores BLE"}
          </button>
        </div>
        <details>
          <summary>Registrar vehículo o banco</summary>
          <form onSubmit={add} className="instrument-toolbar">
            <label>
              Nombre
              <input name="name" required maxLength={150} />
            </label>
            <button disabled={busy || !canWrite}>Guardar vehículo</button>
          </form>
        </details>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>
      <BTMGPAWorkbench token={token} />
      {ble && (
        <BleConnections token={token} vehicles={vehicles} canWrite={canWrite} />
      )}
      <div className="instrument-grid">
        <section className="panel">
          <p className="eyebrow">01 / MANÓMETROS DIGITALES</p>
          <h2>Presión del circuito</h2>
          <span className="badge">{origin}</span>
          <div className="dial-row">
            <Dial name="Baja" reading={low} />
            <Dial name="Alta" reading={high} />
          </div>
          <p className="muted">
            Lecturas históricas con fecha, no conexión activa. Escala visual
            configurable por unidad, sin zonas OEM de normalidad. La presión no
            determina la masa de refrigerante.
          </p>
          <button
            className="ghost"
            disabled={!readings.length}
            onClick={() =>
              downloadJSON(
                { vehicle_id: vehicle, origin, readings },
                "SSScanner-lecturas.json",
              )
            }
          >
            Exportar lecturas
          </button>
        </section>
        <section className="panel">
          <p className="eyebrow">02 / FRECUENCIA</p>
          <h2>Explora la señal eléctrica</h2>
          <div className="big-reading">
            {spectrum?.dominant_frequency_hz == null
              ? "—"
              : spectrum.dominant_frequency_hz.toFixed(2)}{" "}
            <small>Hz</small>
          </div>
          <label>
            Frecuencia de muestreo (Hz)
            <input
              type="number"
              min={0.001}
              max={10000000}
              value={rate}
              onChange={(e) => {
                setRate(Number(e.target.value));
                setSpectrum(null);
              }}
            />
          </label>
          <label>
            Muestras uniformes, separadas por coma
            <textarea
              value={signal}
              onChange={(e) => {
                setSignal(e.target.value);
                setSource("MANUAL_IMPORT");
                setSpectrum(null);
              }}
              placeholder="Importa 32 a 2048 muestras del osciloscopio"
            />
          </label>
          <label>
            Importar archivo de muestras
            <input
              type="file"
              accept=".txt,.csv"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                if (f.size > 60000) {
                  setError("Archivo máximo: 60 KB");
                  return;
                }
                setSignal(await f.text());
                setSource("MANUAL_IMPORT");
                setSpectrum(null);
              }}
            />
          </label>
          <div className="component-buttons">
            <button disabled={busy || !signal} onClick={analyze}>
              Analizar frecuencia
            </button>
            <button className="ghost" onClick={sampleWave}>
              Señal SAMPLE 62.5 Hz
            </button>
          </div>
          <small>Origen: {source}. CSV de una columna, sin encabezado.</small>
          {spectrum && (
            <>
              <p>
                Resolución: {spectrum.resolution_hz.toFixed(3)} Hz · RMS:{" "}
                {spectrum.rms.toFixed(3)} · Pico a pico:{" "}
                {spectrum.peak_to_peak.toFixed(3)}
              </p>
              <p className="muted">{spectrum.limitation}</p>
              <button
                className="ghost"
                onClick={() =>
                  downloadJSON(
                    { spectrum, sample_rate_hz: rate, samples: signal },
                    "SSScanner-frecuencia.json",
                  )
                }
              >
                Exportar análisis
              </button>
            </>
          )}
        </section>
        <section className="panel vision-panel">
          <p className="eyebrow">03 / VISIÓN ARTIFICIAL</p>
          <h2>Reconocimiento de luces</h2>
          <p>
            Tu modelo de Teachable Machine, dentro de un iframe. Inferencia
            local sobre cámara o imagen; las imágenes no se envían al servidor
            de SSScanner. Primero entrena y exporta tu modelo.
          </p>
          <iframe
            className="vision-frame"
            src="/vision-frame.html"
            title="Visor Teachable Machine para luces"
            allow="camera"
            sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
          />
        </section>
      </div>
      <section className="panel">
        <details>
          <summary>Física eléctrica y arquitectura térmica</summary>
          <p>
            El chiller intercambia calor entre refrigerante y líquido de
            refrigeración. Puede coexistir con radiadores: la topología depende
            del vehículo. No se infieren carga de refrigerante, límites de
            presión ni consignas sin documentación OEM.
          </p>
          <form
            className="config-grid"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              void action(async () => {
                setEnergy(
                  await api("/physics/electrical", token, {
                    voltage_v: Number(f.get("v")),
                    current_a: Number(f.get("a")),
                    duration_seconds: Number(f.get("s")),
                  }),
                );
              });
            }}
          >
            <label>
              Tensión DC (V)
              <input
                name="v"
                required
                type="number"
                min={0}
                max={2000}
                step="any"
              />
            </label>
            <label>
              Corriente DC (A)
              <input
                name="a"
                required
                type="number"
                min={-5000}
                max={5000}
                step="any"
              />
            </label>
            <label>
              Duración (s)
              <input
                name="s"
                required
                type="number"
                min={0}
                max={86400}
                step="any"
              />
            </label>
            <button disabled={busy}>Calcular P = V × I</button>
          </form>
          {energy !== null && (
            <pre className="result-json">{JSON.stringify(energy, null, 2)}</pre>
          )}
        </details>
        <details>
          <summary>Accesorio: cable salva memorias OBD2</summary>
          <p>
            Conserva la alimentación durante el cambio de batería. No es una
            interfaz IoT, un escáner ni un programador ECU. La adquisición de
            datos requiere un adaptador compatible y su protocolo. La
            configuración del laboratorio se guarda en SSScanner.
          </p>
        </details>
      </section>
    </>
  );
}
function Dial({ name, reading }: { name: string; reading?: Reading }) {
  const [max, setMax] = useState(500);
  const value = reading?.value,
    angle = -120 + 240 * Math.min(1, Math.max(0, (value ?? 0) / max));
  return (
    <div className="dial">
      <svg
        viewBox="0 0 200 170"
        role="img"
        aria-label={`${name}: ${value ?? "sin datos"} ${reading?.unit || ""}`}
      >
        <circle
          cx="100"
          cy="85"
          r="72"
          fill="#0b201a"
          stroke="#294b41"
          strokeWidth="12"
        />
        {Array.from({ length: 9 }, (_, i) => (
          <line
            key={i}
            x1="100"
            y1="20"
            x2="100"
            y2="28"
            stroke="#70d8b0"
            transform={`rotate(${-120 + i * 30} 100 85)`}
          />
        ))}
        {value != null && (
          <line
            x1="100"
            y1="85"
            x2="100"
            y2="32"
            stroke="#8affc7"
            strokeWidth="3"
            transform={`rotate(${angle} 100 85)`}
          />
        )}
        <circle cx="100" cy="85" r="5" fill="#8affc7" />
        <text x="100" y="126" textAnchor="middle" fill="white" fontSize="22">
          {value == null ? "—" : value.toFixed(1)}
        </text>
        <text x="100" y="147" textAnchor="middle" fill="#9bbeb0" fontSize="12">
          {reading?.unit || "Sin unidad"}
        </text>
      </svg>
      <strong>{name}</strong>
      <small>
        {reading?.observed_at
          ? new Date(reading.observed_at).toLocaleString("es-CO")
          : "Sin captura"}
      </small>
      <label>
        Máximo visual
        <input
          type="number"
          min={1}
          max={100000}
          value={max}
          onChange={(e) => setMax(Math.max(1, Number(e.target.value)))}
        />
      </label>
      {value != null && (value < 0 || value > max) && (
        <small>Fuera de escala visual</small>
      )}
    </div>
  );
}
