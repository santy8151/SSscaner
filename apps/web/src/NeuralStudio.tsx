import { ModelMetrics } from "./ModelMetrics";
import { useEffect, useState, type FormEvent } from "react";
import { api, downloadJSON } from "./api";
type Run = {
  id: string;
  status: string;
  progress: number;
  configuration: unknown;
  result: Record<string, unknown> | null;
};
const models = {
  mlp: [
    "Red neuronal MLP",
    "Clasifica patrones etiquetados. Ajusta capas, nodos, activación, batch y learning rate.",
  ],
  random_forest: [
    "Random Forest",
    "Referencia para datos tabulares etiquetados. Árboles y profundidad; no usa batch ni learning rate.",
  ],
  kmeans: [
    "K-Means",
    "Agrupa estados similares sin etiquetas. Un grupo no equivale a una avería.",
  ],
  pca: [
    "PCA",
    "Reduce variables correlacionadas. No clasifica fallas por sí solo.",
  ],
  isolation_forest: [
    "Isolation Forest",
    "Detecta observaciones atípicas; no confirma un daño.",
  ],
};
const components = {
  system: "Sistema completo",
  compressor: "Compresor",
  condenser: "Condensador",
  evaporator: "Evaporador",
  motor: "Motor",
};
export function NeuralStudio({
  token,
  canWrite,
}: {
  token: string;
  canWrite: boolean;
}) {
  const [model, setModel] = useState<keyof typeof models>("mlp"),
    [component, setComponent] = useState("compressor"),
    [layers, setLayers] = useState([32, 16]);
  const [runs, setRuns] = useState<Run[]>([]),
    [active, setActive] = useState<Run | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const id = active?.id,
    running = active?.status === "queued" || active?.status === "running";
  useEffect(() => {
    let live = true;
    api<Run[]>("/ml/runs", token)
      .then((rows) => {
        if (live) {
          setRuns(rows);
          setActive(rows[0] || null);
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [token]);
  useEffect(() => {
    if (!id || !running) return;
    let live = true;
    const timer = setInterval(() => {
      api<Run>(`/ml/runs/${id}`, token)
        .then((row) => {
          if (live) {
            setActive(row);
            setRuns((old) => [row, ...old.filter((r) => r.id !== row.id)]);
          }
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    }, 1800);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [id, running, token]);
  async function train(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget),
      n = (k: string) => Number(f.get(k));
    const configuration =
      model === "mlp"
        ? {
            model,
            hidden_layers: layers,
            activation: f.get("activation"),
            optimizer: f.get("optimizer"),
            epochs: n("epochs"),
            batch_size: n("batch"),
            learning_rate: n("learning"),
          }
        : model === "random_forest"
          ? { model, trees: n("trees"), max_depth: n("depth") }
          : model === "kmeans"
            ? { model, clusters: n("clusters"), iterations: n("iterations") }
            : model === "pca"
              ? { model, components: n("dimensions") }
              : { model, trees: n("trees"), contamination: n("contamination") };
    setBusy(true);
    setError("");
    try {
      const row = await api<Run>("/ml/runs", token, {
        dataset_origin: "SAMPLE",
        component,
        configuration,
        samples_per_class: n("samples"),
        seed: n("seed"),
      });
      setActive(row);
      setRuns((old) => [row, ...old]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <section className="panel">
        <p className="eyebrow">02 / INTELIGENCIA MODULAR · BTMGPA</p>
        <h2>Configura el análisis por componente</h2>
        <p>
          Dos ramas: visión entrenada en Teachable Machine y análisis de
          señales. Cambiar un módulo modifica el experimento, sin escribir en el
          vehículo.
        </p>
        <div className="component-buttons">
          {Object.entries(components).map(([k, v]) => (
            <button
              key={k}
              className={component === k ? "" : "ghost"}
              onClick={() => setComponent(k)}
            >
              {v}
            </button>
          ))}
        </div>
        <p className="muted">
          El componente selecciona las variables de entrada. Las siete etiquetas
          siguen siendo escenarios sintéticos del sistema.
        </p>
      </section>
      <div className="model-layout">
        <form className="panel" onSubmit={train}>
          <label>
            Modelo
            <select
              aria-label="Modelo"
              value={model}
              onChange={(e) => setModel(e.target.value as keyof typeof models)}
            >
              {Object.entries(models).map(([k, v]) => (
                <option key={k} value={k}>
                  {v[0]}
                </option>
              ))}
            </select>
          </label>
          <p>{models[model][1]}</p>
          {model === "mlp" && (
            <>
              <div className="network" aria-label="Capas de la red neuronal">
                <div>
                  <strong>Entrada</strong>
                  <small>
                    {component === "system"
                      ? 9
                      : component === "compressor"
                        ? 4
                        : 3}{" "}
                    variables*
                  </small>
                </div>
                {layers.map((w, i) => (
                  <div className="layer" key={i}>
                    <span>Capa {i + 1}</span>
                    <div className="neurons">
                      {Array.from({ length: Math.min(w, 12) }, (_, j) => (
                        <i key={j} />
                      ))}
                    </div>
                    <label>
                      Nodos capa {i + 1}
                      <input
                        required
                        type="number"
                        min={4}
                        max={128}
                        value={w}
                        onChange={(e) =>
                          setLayers((old) =>
                            old.map((v, j) =>
                              i === j ? Number(e.target.value) : v,
                            ),
                          )
                        }
                      />
                    </label>
                  </div>
                ))}
                <div>
                  <strong>Salida</strong>
                  <small>7 escenarios</small>
                </div>
              </div>
              <p className="muted">
                Vista resumida: hasta 12 nodos dibujados por capa. *Se añaden
                indicadores de datos ausentes. Activación compartida entre
                capas.
              </p>
              <div className="component-buttons">
                <button
                  type="button"
                  className="ghost"
                  disabled={layers.length === 3}
                  onClick={() => setLayers([...layers, 16])}
                >
                  + Añadir capa
                </button>
                <button
                  type="button"
                  className="ghost"
                  disabled={layers.length === 1}
                  onClick={() => setLayers(layers.slice(0, -1))}
                >
                  − Quitar capa
                </button>
              </div>
            </>
          )}
          <div className="config-grid" key={model}>
            {model === "mlp" && (
              <>
                <label>
                  Activación
                  <select name="activation">
                    <option>relu</option>
                    <option>tanh</option>
                    <option>logistic</option>
                  </select>
                </label>
                <label>
                  Optimizador
                  <select name="optimizer">
                    <option>adam</option>
                    <option>sgd</option>
                  </select>
                </label>
                <NumberField
                  label="Épocas"
                  name="epochs"
                  value={30}
                  min={1}
                  max={300}
                />
                <NumberField
                  label="Batch size"
                  name="batch"
                  value={32}
                  min={8}
                  max={256}
                />
                <NumberField
                  label="Learning rate"
                  name="learning"
                  value={0.001}
                  min={0.00001}
                  max={0.1}
                  step="any"
                />
              </>
            )}
            {(model === "random_forest" || model === "isolation_forest") && (
              <NumberField
                label="Árboles"
                name="trees"
                value={80}
                min={10}
                max={200}
              />
            )}
            {model === "random_forest" && (
              <NumberField
                label="Profundidad máxima"
                name="depth"
                value={8}
                min={2}
                max={30}
              />
            )}
            {model === "kmeans" && (
              <>
                <NumberField
                  label="Grupos K"
                  name="clusters"
                  value={4}
                  min={2}
                  max={12}
                />
                <NumberField
                  label="Iteraciones máximas"
                  name="iterations"
                  value={100}
                  min={10}
                  max={300}
                />
              </>
            )}
            {model === "pca" && (
              <NumberField
                label="Componentes principales"
                name="dimensions"
                value={2}
                min={1}
                max={3}
              />
            )}
            {model === "isolation_forest" && (
              <NumberField
                label="Fracción esperada de atípicos"
                name="contamination"
                value={0.05}
                min={0.001}
                max={0.3}
                step="any"
              />
            )}
            <NumberField
              label="Muestras por escenario"
              name="samples"
              value={60}
              min={25}
              max={150}
            />
            <NumberField
              label="Semilla"
              name="seed"
              value={42}
              min={0}
              max={2147483647}
            />
          </div>
          <p className="muted">
            75% entrenamiento / 25% prueba. Preprocesamiento ajustado solo al
            entrenamiento. El servidor guarda modelo, configuración y métricas.
          </p>
          <button disabled={busy || running || !canWrite}>
            {running ? "Entrenamiento en curso…" : "Entrenar y guardar SAMPLE"}
          </button>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>
        <section className="panel">
          <h2>Experimento guardado</h2>
          {active ? (
            <>
              <span className="badge">{active.status}</span>
              <progress
                value={active.progress}
                max={100}
                aria-label="Progreso de entrenamiento"
              />
              <p className="muted">SAMPLE · Sin validación en vehículos</p>
              <ModelMetrics result={active.result} />
              <details>
                <summary>Configuración y evidencia del experimento</summary>
                <pre className="result-json">
                  {JSON.stringify(
                    {
                      configuration: active.configuration,
                      result: active.result,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
              <button
                className="ghost"
                onClick={() =>
                  downloadJSON(active, `SSScanner-model-${active.id}.json`)
                }
              >
                Exportar experimento
              </button>
            </>
          ) : (
            <p>Selecciona un componente y entrena un modelo.</p>
          )}
          <label>
            Historial
            <select
              value={active?.id || ""}
              onChange={(e) =>
                setActive(runs.find((r) => r.id === e.target.value) || null)
              }
            >
              <option value="">Selecciona</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id.slice(0, 8)} · {r.status}
                </option>
              ))}
            </select>
          </label>
        </section>
      </div>
      <section className="panel">
        <h2>Rama de visión · Teachable Machine</h2>
        <p>
          Entrena clases: luz encendida, apagada y reflejo/indeterminado.
          Exporta el modelo TensorFlow.js y pega su enlace en Instrumentos.
          Valida con iluminación y vehículos distintos.
        </p>
        <a
          href="https://teachablemachine.withgoogle.com/train/image"
          target="_blank"
          rel="noreferrer"
        >
          Abrir entrenamiento en Teachable Machine ↗
        </a>
        <p>
          Los cinco métodos cubren tareas distintas, sin ganador universal.
          K-Means y PCA son módulos de análisis; no tipos de neuronas.
        </p>
      </section>
    </>
  );
}
function NumberField({
  label,
  name,
  value,
  min,
  max,
  step = "1",
}: {
  label: string;
  name: string;
  value: number;
  min: number;
  max: number;
  step?: string;
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        required
        type="number"
        defaultValue={value}
        min={min}
        max={max}
        step={step}
      />
    </label>
  );
}
