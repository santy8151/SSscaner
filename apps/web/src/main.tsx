import { useEffect, useState, type FormEvent } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowUpRight,
  Car,
  ChevronRight,
  CircleGauge,
  ClipboardList,
  Cpu,
  Download,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  LogOut,
  Radio,
  Settings,
  ShieldCheck,
  Snowflake,
  Users,
  Wrench,
  Zap,
  Bluetooth,
  BrainCircuit,
} from "lucide-react";
import "./styles.css";
import "./beta.css";
import { api } from "./api";
import { BetaHub } from "./BetaHub";
import { BleConnections } from "./BleConnections";
import { NeuralLab } from "./NeuralLab";

type Vehicle = {
  id: string;
  name: string;
  kind: string;
  manufacturer: string | null;
  model: string | null;
  year: number | null;
};
type Reading = {
  signal: string;
  value: number | null;
  unit: string;
  quality: string;
};
type Batch = {
  origin: string;
  readings: Reading[];
  dtcs: string[];
  observed_at: string;
};
type Scan = {
  id: string;
  vehicle_id: string;
  scenario: string;
  protocol: string;
  origin: string;
  created_at: string;
  batches?: Batch[];
};
type Diagnosis = {
  status: string;
  confidence: null;
  recommendations: string[];
  evidence: {
    available_signals: number;
    missing_signals: string[];
    dtcs: string[];
  };
};
type Calibration = { status: string; message: string; missing: string[] };
type Session = { access_token: string; user: { email: string; role: string } };
const navigation = [
  ["/beta", "BETA / Demo", FlaskConical],
  ["/dashboard", "Resumen", LayoutDashboard],
  ["/vehicles", "Vehículos", Car],
  ["/electricity", "Electricidad", Zap],
  ["/turbo", "Performance / Turbo", Activity],
  ["/machines", "Maquinaria", Wrench],
  ["/scanner", "Escáner", Radio],
  ["/connections", "Conexiones BLE", Bluetooth],
  ["/models", "Modelos / IA", BrainCircuit],
  ["/live-data", "Datos en vivo", Activity],
  ["/diagnostics", "Diagnóstico", FlaskConical],
  ["/calibration", "Calibración", CircleGauge],
  ["/maintenance", "Mantenimiento", ClipboardList],
  ["/customers", "Clientes", Users],
  ["/reports", "Reportes", Download],
  ["/settings", "Configuración", Settings],
] as const;
const scenarioNames: Record<string, string> = {
  normal: "Normal · SAMPLE",
  low_refrigerant: "Bajo refrigerante · SAMPLE",
  overcharge: "Sobrecarga · SAMPLE",
  condenser_airflow: "Flujo de condensador · SAMPLE",
  fan_fault: "Fallo de ventilador · SAMPLE",
  compressor_fault: "Fallo de compresor · SAMPLE",
  sensor_fault: "Fallo de sensor · SAMPLE",
  disconnected: "Desconectado · SAMPLE",
};
const signalNames: Record<string, string> = {
  rpm: "RPM del motor",
  engine_temperature: "Temperatura motor",
  voltage: "Tensión eléctrica",
  low_pressure: "Presión de baja",
  high_pressure: "Presión de alta",
  ambient_temperature: "Temperatura ambiente",
  evaporator_temperature: "Temperatura evaporador",
  compressor_on: "Compresor",
  fan_on: "Ventilador",
};
function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [register, setRegister] = useState(false);
  const [path, setPath] = useState(
    location.pathname === "/" ? "/dashboard" : location.pathname,
  );
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [selected, setSelected] = useState("");
  const [scan, setScan] = useState<Scan | null>(null);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [calibration, setCalibration] = useState<Calibration | null>(null);
  const [scenario, setScenario] = useState("normal");
  const [protocol, setProtocol] = useState("J1939");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [apiReady, setApiReady] = useState(false);
  const token = session?.access_token || "";
  const canWrite = session?.user.role !== "viewer";
  const vehicle = vehicles.find((item) => item.id === selected);
  const latest = scan?.batches?.at(-1);
  const readings = latest?.readings || [];
  useEffect(() => {
    const listener = () => setPath(location.pathname);
    window.addEventListener("popstate", listener);
    return () => window.removeEventListener("popstate", listener);
  }, []);
  useEffect(() => {
    fetch("/ready", { signal: AbortSignal.timeout(5000) })
      .then((response) => setApiReady(response.ok))
      .catch(() => setApiReady(false));
  }, []);
  useEffect(() => {
    if (!token) return;
    let active = true;
    Promise.all([
      api<Vehicle[]>("/vehicles", token),
      api<Scan[]>("/scans", token),
    ])
      .then(([items, history]) => {
        if (active) {
          setVehicles(items);
          setScans(history);
          setSelected(items[0]?.id || "");
        }
      })
      .catch((failure) => {
        if (active) setError(failure.message);
      });
    return () => {
      active = false;
    };
  }, [token]);
  function navigate(next: string) {
    history.pushState({}, "", next);
    setPath(next);
    setError("");
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Ocurrió un error");
    } finally {
      setBusy(false);
    }
  }
  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await run(async () => {
      const result = await api<Session>(
        register ? "/auth/register" : "/auth/login",
        "",
        Object.fromEntries(form),
      );
      setSession(result);
    });
  }
  async function addVehicle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    await run(async () => {
      const item = await api<Vehicle>("/vehicles", token, data);
      setVehicles((previous) => [item, ...previous]);
      setSelected(item.id);
      setScan(null);
      setDiagnosis(null);
      setCalibration(null);
      form.reset();
    });
  }
  async function simulate() {
    await run(async () => {
      const result = await api<Scan>("/simulator/scans", token, {
        vehicle_id: selected,
        scenario,
        protocol,
      });
      setScan(result);
      setDiagnosis(null);
      setCalibration(null);
      setScans((previous) => [result, ...previous]);
      navigate("/dashboard");
    });
  }
  function chooseVehicle(id: string) {
    setSelected(id);
    setScan(null);
    setDiagnosis(null);
    setCalibration(null);
  }
  async function loadScan(item: Scan) {
    await run(async () => {
      setScan(await api<Scan>(`/scans/${item.id}`, token));
      setSelected(item.vehicle_id);
      setDiagnosis(null);
      setCalibration(null);
      navigate("/dashboard");
    });
  }
  function download() {
    if (!scan) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify({ scan, diagnosis, calibration }, null, 2)], {
        type: "application/json",
      }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `SSScanner-SAMPLE-${scan.id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function startBetaDemo() {
    await run(async () => {
      let demo = vehicles.find(
        (item) => item.name === "Equipo demo BETA (SAMPLE)",
      );
      if (!demo) {
        demo = await api<Vehicle>("/vehicles", token, {
          name: "Equipo demo BETA (SAMPLE)",
          kind: "machinery",
        });
        setVehicles((old) => [demo!, ...old]);
      }
      const capture = await api<Scan>("/simulator/scans", token, {
        vehicle_id: demo.id,
        scenario: "condenser_airflow",
        protocol: "J1939",
      });
      setSelected(demo.id);
      setScan(capture);
      setScans((old) => [capture, ...old]);
      setScenario("condenser_airflow");
      setProtocol("J1939");
      setDiagnosis(null);
      setCalibration(null);
      navigate("/dashboard");
    });
  }
  async function logout() {
    await run(async () => {
      try {
        await api("/auth/logout", token, {});
      } finally {
        setSession(null);
        setVehicles([]);
        setScans([]);
        setScan(null);
        setDiagnosis(null);
        setCalibration(null);
      }
    });
  }
  if (!session)
    return (
      <div className="access">
        <section className="access-story">
          <div className="logo">
            <Cpu /> SS<span>Scanner</span>
            <sup>BETA</sup>
          </div>
          <p className="eyebrow">INTELIGENCIA TÉCNICA PARA TU TALLER</p>
          <h1>
            Entiende el sistema.
            <br />
            <em>Decide con evidencia.</em>
          </h1>
          <p>
            Una base para conectar diagnóstico, datos y mantenimiento de
            vehículos y maquinaria.
          </p>
          <div className="access-features">
            <span>
              <Activity />
              Telemetría trazable
            </span>
            <span>
              <ShieldCheck />
              Calibración con fuentes
            </span>
            <span>
              <Wrench />
              Diseñado para técnicos
            </span>
          </div>
          <small>
            FASE 1 · Simulador SAMPLE · Sin conexión a hardware real
          </small>
        </section>
        <form className="access-form" onSubmit={authenticate}>
          <span className="badge">ESPACIO DE TRABAJO</span>
          <h2>
            {register ? "Crea tu taller local" : "Bienvenido a SSScanner"}
          </h2>
          <p>Accede a tu laboratorio de desarrollo.</p>
          <label>
            Identificador de empresa
            <input
              name="organization"
              required
              minLength={3}
              maxLength={80}
              pattern="[a-z0-9][a-z0-9-]+[a-z0-9]"
              placeholder="mi-taller"
              autoComplete="organization"
            />
          </label>
          <label>
            Correo electrónico
            <input
              name="email"
              type="email"
              required
              maxLength={254}
              placeholder="tecnico@taller.com"
              autoComplete="username"
            />
          </label>
          <label>
            Contraseña
            <input
              name="password"
              type="password"
              required
              minLength={12}
              maxLength={128}
              placeholder="Mínimo 12 caracteres"
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          <button disabled={busy}>
            {busy
              ? "Procesando…"
              : register
                ? "Crear empresa local"
                : "Entrar al laboratorio"}
            <ArrowUpRight size={16} />
          </button>
          <button
            type="button"
            className="ghost"
            onClick={() => {
              setRegister(!register);
              setError("");
            }}
          >
            {register
              ? "Ya tengo una cuenta"
              : "Crear empresa · solo desarrollo"}
          </button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <small>
            La sesión vive en esta pestaña. Al recargar, inicia sesión de nuevo.
            Las cuentas y mediciones se guardan en la base local.
          </small>
        </form>
      </div>
    );
  const pageTitle =
    navigation.find((item) => item[0] === path)?.[1] || "Página no encontrada";
  const showWorkspace = [
    "/dashboard",
    "/scanner",
    "/live-data",
    "/diagnostics",
    "/calibration",
  ].includes(path);
  return (
    <div className="app">
      <aside className="sidebar">
        <a
          href="/dashboard"
          className="logo"
          onClick={(event) => {
            event.preventDefault();
            navigate("/dashboard");
          }}
        >
          <Cpu size={25} />
          SS<span>Scanner</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">ST</span>
          <div>
            Taller de desarrollo<small>{session.user.role}</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav>
          {navigation.map(([href, label, Icon]) => (
            <a
              key={href}
              href={href}
              className={path === href ? "active" : ""}
              onClick={(event) => {
                event.preventDefault();
                navigate(href);
              }}
            >
              <Icon size={17} />
              {label}
              {href === "/scanner" && <span className="mini">LAB</span>}
            </a>
          ))}
        </nav>
        <div className="side-foot">
          <span className="dot" /> Entorno de desarrollo
          <small>v0.2 · BETA técnica</small>
          <button className="ghost" onClick={logout} disabled={busy}>
            <LogOut size={15} />
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div>
            WORKSPACE <ChevronRight size={12} /> <strong>{pageTitle}</strong>
          </div>
          <button className="beta-button" onClick={() => navigate("/beta")}>
            <FlaskConical size={14} />
            BETA
          </button>
          <span className={apiReady ? "status" : "status offline"}>
            <span className="dot" />
            {apiReady ? "API disponible" : "API no disponible"}
          </span>
        </header>
        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}
        <div className="title-row">
          <div>
            <p className="eyebrow">LABORATORIO AUTOMOTRIZ / FASE 1</p>
            <h1>
              {path === "/dashboard" ? "Tu taller, en perspectiva." : pageTitle}
            </h1>
            <p className="muted">
              {path === "/dashboard"
                ? "Una vista clara de tus equipos y de la evidencia técnica."
                : "Base funcional de SSScanner. Cada módulo muestra su estado real."}
            </p>
          </div>
          <span className="badge sample">
            {path === "/connections"
              ? "BLE · SOLO LECTURA"
              : path === "/models"
                ? "ML · DATASET SAMPLE"
                : path === "/beta"
                  ? "BETA TÉCNICA"
                  : "SAMPLE · LABORATORIO"}
          </span>
        </div>
        <div className="stats">
          <div>
            <span>
              Equipos registrados
              <Car size={17} />
            </span>
            <strong>{vehicles.length.toString().padStart(2, "0")}</strong>
            <small>En tu organización</small>
          </div>
          <div>
            <span>
              Sesiones de laboratorio
              <Radio size={17} />
            </span>
            <strong>{scans.length.toString().padStart(2, "0")}</strong>
            <small>Capturas SAMPLE guardadas</small>
          </div>
          <div>
            <span>
              Conexiones de campo
              <Zap size={17} />
            </span>
            <strong>BLE</strong>
            <small>Ver estado en Conexiones BLE</small>
          </div>
          <div>
            <span>
              Fuentes OEM
              <ShieldCheck size={17} />
            </span>
            <strong className="small-stat">SOURCE_REQUIRED</strong>
            <small>Ninguna especificación aprobada</small>
          </div>
        </div>
        {path === "/beta" && (
          <BetaHub
            token={token}
            onNavigate={navigate}
            onDemo={startBetaDemo}
            busy={busy}
            canWrite={canWrite}
          />
        )}
        {path === "/connections" && (
          <BleConnections
            token={token}
            vehicles={vehicles}
            canWrite={canWrite}
          />
        )}
        {path === "/models" && <NeuralLab token={token} canWrite={canWrite} />}
        {path === "/vehicles" && (
          <section className="panel">
            <div className="panel-head">
              <h2>Vehículos y equipos</h2>
              <span className="badge">PERSISTENCIA ACTIVA</span>
            </div>
            <form onSubmit={addVehicle} className="vehicle-form">
              <label>
                Nombre / identificación
                <input
                  name="name"
                  required
                  maxLength={150}
                  placeholder="Ej. Unidad de pruebas 01"
                />
              </label>
              <label>
                Clase
                <select name="kind">
                  <option value="light">Vehículo liviano</option>
                  <option value="heavy">Vehículo pesado</option>
                  <option value="machinery">Maquinaria amarilla</option>
                </select>
              </label>
              <button disabled={busy || !canWrite}>
                Registrar equipo <ArrowUpRight size={15} />
              </button>
            </form>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>EQUIPO</th>
                    <th>CLASE</th>
                    <th>IDENTIFICADOR</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicles.map((item) => (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      <td>{item.kind}</td>
                      <td className="mono">{item.id.slice(0, 8)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {vehicles.length === 0 && (
              <p className="empty">
                Registra el primer equipo para iniciar una simulación.
              </p>
            )}
          </section>
        )}
        {showWorkspace && (
          <>
            <section className="panel connection">
              <div className="panel-head">
                <h2>
                  <Radio size={17} />
                  Estación de diagnóstico
                </h2>
                <span className="muted">Conexión simulada explícita</span>
              </div>
              <div className="connection-grid">
                <label>
                  Equipo actual
                  <select
                    value={selected}
                    disabled={busy}
                    onChange={(event) => chooseVehicle(event.target.value)}
                  >
                    <option value="" disabled>
                      Selecciona un equipo
                    </option>
                    {vehicles.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Escenario de prueba
                  <select
                    value={scenario}
                    disabled={busy}
                    onChange={(event) => setScenario(event.target.value)}
                  >
                    {Object.entries(scenarioNames).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Protocolo (metadato)
                  <select
                    value={protocol}
                    disabled={busy}
                    onChange={(event) => setProtocol(event.target.value)}
                  >
                    <option>J1939</option>
                    <option>OBD-II</option>
                    <option>CAN</option>
                    <option>EXTERNAL</option>
                  </select>
                </label>
                <button
                  onClick={simulate}
                  disabled={busy || !selected || !canWrite}
                >
                  <Radio size={15} />
                  {busy ? "Procesando…" : "Iniciar simulación"}
                </button>
              </div>
              {!vehicles.length && (
                <button
                  className="text-button"
                  onClick={() => navigate("/vehicles")}
                >
                  + Registra tu primer equipo para comenzar
                </button>
              )}
            </section>
            <div className="work-grid">
              <section className="panel telemetry">
                <div className="panel-head">
                  <h2>
                    <Activity size={17} />
                    Telemetría A/C
                  </h2>
                  <span className="badge">
                    {latest ? "CAPTURA SAMPLE" : "SIN CAPTURA"}
                  </span>
                </div>
                <div className="signal-intro">
                  <div>
                    <span className="muted">
                      {vehicle?.name || "Ningún equipo seleccionado"}
                    </span>
                    <h3>
                      {scan
                        ? scenarioNames[scan.scenario]
                        : "Tu próxima lectura comienza aquí"}
                    </h3>
                  </div>
                  <Snowflake className="snowflake" size={46} />
                </div>
                <div className="wave" aria-hidden="true">
                  <svg viewBox="0 0 600 90" preserveAspectRatio="none">
                    <defs>
                      <pattern
                        id="grid"
                        width="30"
                        height="22"
                        patternUnits="userSpaceOnUse"
                      >
                        <path
                          d="M30 0H0V22"
                          fill="none"
                          stroke="#23353d"
                          strokeWidth="1"
                        />
                      </pattern>
                    </defs>
                    <rect width="600" height="90" fill="url(#grid)" />
                    <path
                      d="M0 52H45L60 44L72 66L92 16L111 78L128 45L148 52H205L220 44L233 66L253 16L272 78L289 45L309 52H367L382 44L395 66L415 16L434 78L451 45L471 52H529L544 44L557 66L577 16L596 78"
                      fill="none"
                      stroke="#6ae9c1"
                      strokeWidth="2"
                    />
                  </svg>
                  <small>GRÁFICA ILUSTRATIVA · NO ES UNA SEÑAL MEDIDA</small>
                </div>
                <div className="readings">
                  {[
                    "low_pressure",
                    "high_pressure",
                    "ambient_temperature",
                    "rpm",
                  ].map((signal) => {
                    const item = readings.find(
                      (reading) => reading.signal === signal,
                    );
                    return (
                      <div key={signal}>
                        <span>{signalNames[signal]}</span>
                        <strong>
                          {item?.value ?? "—"} <small>{item?.unit || ""}</small>
                        </strong>
                      </div>
                    );
                  })}
                </div>
                <p className="muted note">
                  {latest
                    ? `Última captura: ${new Date(latest.observed_at).toLocaleString("es-CO")}. Valores ficticios para desarrollo; no son límites de servicio.`
                    : "Inicia una simulación para guardar una captura. No hay lecturas reales conectadas."}
                </p>
              </section>
              <section className="panel calibration">
                <div className="panel-head">
                  <h2>
                    <ShieldCheck size={17} />
                    Calibration Profile
                  </h2>
                </div>
                <div className="shield">
                  <ShieldCheck size={34} />
                </div>
                <span className="badge warning">SOURCE_REQUIRED</span>
                <h3>
                  La precisión empieza
                  <br />
                  en la fuente.
                </h3>
                <p>
                  La calibración requiere una ficha OEM validada. La IA no
                  define cargas ni parámetros críticos.
                </p>
                <dl>
                  <div>
                    <dt>Refrigerante</dt>
                    <dd>Pendiente de fuente</dd>
                  </div>
                  <div>
                    <dt>Carga especificada</dt>
                    <dd>— g</dd>
                  </div>
                  <div>
                    <dt>Aceite / vacío</dt>
                    <dd>Sin especificación</dd>
                  </div>
                </dl>
                <button
                  className="secondary"
                  disabled={busy || !selected || !canWrite}
                  onClick={() =>
                    run(async () =>
                      setCalibration(
                        await api<Calibration>("/calibration/evaluate", token, {
                          vehicle_id: selected,
                        }),
                      ),
                    )
                  }
                >
                  Comprobar requisitos <ChevronRight size={15} />
                </button>
                {calibration && (
                  <p className="result-note" role="status">
                    {calibration.message}
                  </p>
                )}
              </section>
            </div>
            <div className="work-grid bottom-grid">
              <section className="panel">
                <div className="panel-head">
                  <h2>
                    <FlaskConical size={17} />
                    Diagnosis Engine
                  </h2>
                  <span className="badge">CONTRATO INICIAL</span>
                </div>
                <p className="muted">
                  Primero evidencia y reglas revisadas. Después, modelos
                  validados.
                </p>
                <button
                  className="secondary"
                  onClick={() =>
                    run(async () => {
                      if (scan)
                        setDiagnosis(
                          await api<Diagnosis>("/diagnostics", token, {
                            scan_id: scan.id,
                          }),
                        );
                    })
                  }
                  disabled={busy || !scan || !canWrite}
                >
                  Revisar evidencia <ArrowUpRight size={15} />
                </button>
                {diagnosis ? (
                  <div className="diagnosis-result" role="status">
                    <strong>{diagnosis.status}</strong>
                    <p>
                      {diagnosis.evidence.available_signals} señales ·{" "}
                      {diagnosis.evidence.missing_signals.length} ausentes ·
                      Confianza: no estimada
                    </p>
                    {diagnosis.recommendations.map((text) => (
                      <p key={text}>{text}</p>
                    ))}
                  </div>
                ) : (
                  <p className="note muted">
                    Sin diagnósticos de avería. No se muestran porcentajes sin
                    validación.
                  </p>
                )}
              </section>
              <section className="panel">
                <div className="panel-head">
                  <h2>
                    <Gauge size={17} />
                    Estado de captura
                  </h2>
                </div>
                <div className="state-line">
                  <span>Protocolo seleccionado</span>
                  <strong>{scan?.protocol || "—"}</strong>
                </div>
                <div className="state-line">
                  <span>Origen de datos</span>
                  <strong>{scan?.origin || "Sin sesión"}</strong>
                </div>
                <div className="state-line">
                  <span>Códigos DTC de prueba</span>
                  <strong>{latest?.dtcs.join(", ") || "Sin registros"}</strong>
                </div>
                <button
                  className="text-button"
                  onClick={download}
                  disabled={!scan}
                >
                  <Download size={14} />
                  Descargar sesión JSON
                </button>
              </section>
            </div>
            {path === "/live-data" && (
              <section className="panel">
                <h2>Señales de la última captura</h2>
                <p className="muted">
                  Esta fase muestra snapshots. Streaming continuo pendiente.
                </p>
                {readings.map((item) => (
                  <div className="state-line" key={item.signal}>
                    <span>{signalNames[item.signal]}</span>
                    <strong>
                      {item.value ?? "MISSING"} {item.unit} · {item.quality}
                    </strong>
                  </div>
                ))}
              </section>
            )}
          </>
        )}
        {path === "/reports" && (
          <section className="panel">
            <div className="panel-head">
              <h2>Historial de sesiones</h2>
              <span className="badge">SAMPLE</span>
            </div>
            {scans.length === 0 ? (
              <p className="empty">No hay sesiones guardadas.</p>
            ) : (
              scans.map((item) => (
                <button
                  className="history-row"
                  key={item.id}
                  onClick={() => loadScan(item)}
                  disabled={busy}
                >
                  <div>
                    <strong>
                      {vehicles.find((v) => v.id === item.vehicle_id)?.name ||
                        item.vehicle_id.slice(0, 8)}
                    </strong>
                    <small>
                      {scenarioNames[item.scenario]} ·{" "}
                      {new Date(item.created_at).toLocaleString("es-CO")}
                    </small>
                  </div>
                  <span>
                    {item.protocol} <ChevronRight size={14} />
                  </span>
                </button>
              ))
            )}
          </section>
        )}
        {["/machines", "/maintenance", "/customers", "/settings"].includes(
          path,
        ) && (
          <section className="panel planned">
            <div className="shield">
              <Wrench size={28} />
            </div>
            <span className="badge">SIGUIENTE FASE</span>
            <h2>{pageTitle}: contrato definido</h2>
            <p>
              Este módulo forma parte de la arquitectura aprobada. Su flujo
              operativo todavía no está implementado.
            </p>
            {path === "/machines" && (
              <button onClick={() => navigate("/vehicles")}>
                Registrar maquinaria como equipo
              </button>
            )}
            {path === "/settings" && (
              <p>
                Rol actual: {session.user.role}. Gestión de miembros disponible
                por API para administradores. Conexiones BLE de solo lectura
                disponibles según el dispositivo y su protocolo.
              </p>
            )}
          </section>
        )}
        {!navigation.some((item) => item[0] === path) && (
          <section className="panel">
            <h2>Página no encontrada</h2>
            <button onClick={() => navigate("/dashboard")}>
              Volver al resumen
            </button>
          </section>
        )}
        <footer>
          <span>SSScanner · Ingeniería con evidencia.</span>
          <span>FASE 1 / SAMPLE ≠ DATOS OEM</span>
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
