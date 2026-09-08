import { useEffect, useState, type FormEvent } from "react";
import { createRoot } from "react-dom/client";
import { Cpu, Gauge, BrainCircuit, LogOut, FlaskConical } from "lucide-react";
import { api } from "./api";
import { NeuralStudio } from "./NeuralStudio";
import { Instruments } from "./Instruments";
import "./styles.css";
import "./beta.css";
import "./studio.css";
type Session = { access_token: string; user: { email: string; role: string } };
function App() {
  const [session, setSession] = useState<Session | null>(null),
    [register, setRegister] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [beta, setBeta] = useState(false),
    [path, setPath] = useState(location.pathname),
    [ready, setReady] = useState(false);
  useEffect(() => {
    const listener = () => setPath(location.pathname);
    window.addEventListener("popstate", listener);
    fetch("/ready")
      .then((r) => setReady(r.ok))
      .catch(() => setReady(false));
    return () => window.removeEventListener("popstate", listener);
  }, []);
  function navigate(to: string) {
    history.pushState({}, "", to);
    setPath(to);
    window.scrollTo(0, 0);
  }
  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fields = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    setError("");
    try {
      setSession(
        await api<Session>(
          register ? "/auth/register" : "/auth/login",
          "",
          fields,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    if (session)
      try {
        await api("/auth/logout", session.access_token, {});
      } catch {
        /* Clear local access even if server is unavailable. */
      } finally {
        setSession(null);
      }
  }
  if (!session)
    return (
      <div className="access">
        <section className="access-story">
          <div className="logo">
            <Cpu />
            SS<span>Scanner</span>
            <sup>BETA</sup>
          </div>
          <p className="eyebrow">INGENIERÍA AUTOMOTRIZ / BTMGPA</p>
          <h1>
            Mide el sistema.
            <br />
            <em>Comprende la señal.</em>
          </h1>
          <p>
            Instrumentos, visión y modelos configurables para explorar el
            diagnóstico térmico y eléctrico.
          </p>
          <div className="access-features">
            <span>
              <Gauge />
              Tres instrumentos
            </span>
            <span>
              <BrainCircuit />
              Cinco métodos de análisis
            </span>
          </div>
          <small>BETA técnica · Validación de hardware pendiente</small>
        </section>
        <form className="access-form" onSubmit={login}>
          <span className="badge">LABORATORIO</span>
          <h2>{register ? "Crear taller local" : "Entrar a SSScanner"}</h2>
          <label>
            Identificador de empresa
            <input
              required
              name="organization"
              minLength={3}
              maxLength={80}
              autoComplete="organization"
            />
          </label>
          <label>
            Correo electrónico
            <input required name="email" type="email" autoComplete="username" />
          </label>
          <label>
            Contraseña
            <input
              required
              name="password"
              type="password"
              minLength={12}
              maxLength={128}
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          <button disabled={busy}>
            {busy ? "Procesando…" : "Entrar al laboratorio"}
          </button>
          <button
            className="ghost"
            type="button"
            onClick={() => setRegister(!register)}
          >
            {register ? "Ya tengo cuenta" : "Crear empresa · solo desarrollo"}
          </button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <small>
            Sesión en esta pestaña. Cuentas, lecturas BLE y experimentos
            guardados en el servidor.
          </small>
        </form>
      </div>
    );
  const allowed = ["/", "/instruments", "/models"].includes(path),
    models = path === "/models";
  return (
    <div className="app">
      <aside className="sidebar">
        <a
          href="/instruments"
          className="logo"
          onClick={(e) => {
            e.preventDefault();
            navigate("/instruments");
          }}
        >
          <Cpu />
          SS<span>Scanner</span>
        </a>
        <p className="nav-label">BETA / DOS ESPACIOS</p>
        <nav>
          <a
            className={!models ? "active" : ""}
            href="/instruments"
            onClick={(e) => {
              e.preventDefault();
              navigate("/instruments");
            }}
          >
            <Gauge />
            Instrumentos
          </a>
          <a
            className={models ? "active" : ""}
            href="/models"
            onClick={(e) => {
              e.preventDefault();
              navigate("/models");
            }}
          >
            <BrainCircuit />
            Redes neuronales
          </a>
        </nav>
        <div className="side-foot">
          <small>Otras páginas bloqueadas en esta beta.</small>
          <small>{session.user.role}</small>
          <button className="ghost" onClick={logout}>
            <LogOut />
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main>
        <header>
          <strong>
            BTMGPA / {models ? "Redes neuronales" : "Instrumentos"}
          </strong>
          <button className="beta-button" onClick={() => setBeta(!beta)}>
            <FlaskConical size={16} />
            BETA
          </button>
          <span className="status">
            {ready ? "API disponible" : "API no disponible"}
          </span>
        </header>
        {beta && (
          <section className="panel">
            <h2>Avance técnico para demostración</h2>
            <p>
              Lectura BLE configurable, cinco métodos ejecutables sobre SAMPLE,
              importación de señales y visor de modelos de visión. Requiere
              validar sensores, datasets y especificaciones OEM antes de
              diagnóstico en taller. Sin control físico ni escritura ECU.
            </p>
            <button className="ghost" onClick={() => setBeta(false)}>
              Cerrar información beta
            </button>
          </section>
        )}
        {allowed ? (
          <>
            <div className="title-row">
              <div>
                <p className="eyebrow">SSSCANNER / LABORATORIO DE SEÑALES</p>
                <h1>
                  {models
                    ? "La inteligencia, en tus manos."
                    : "Cada señal tiene una historia."}
                </h1>
                <p className="muted">
                  {models
                    ? "Configura, entrena y conserva evidencia."
                    : "Manómetros · Frecuencia · Reconocimiento de luces"}
                </p>
              </div>
              <span className="badge">BETA 0.3</span>
            </div>
            {models ? (
              <NeuralStudio
                token={session.access_token}
                canWrite={session.user.role !== "viewer"}
              />
            ) : (
              <Instruments
                token={session.access_token}
                canWrite={session.user.role !== "viewer"}
              />
            )}
          </>
        ) : (
          <section className="panel">
            <h2>Página bloqueada en esta beta</h2>
            <button onClick={() => navigate("/instruments")}>
              Volver a Instrumentos
            </button>
          </section>
        )}
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
