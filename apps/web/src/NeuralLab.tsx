import { useEffect, useState, type FormEvent } from "react";
import { BrainCircuit, Download, Play } from "lucide-react";
import { api, downloadJSON } from "./api";

type Run = {
  id: string;
  status: string;
  progress: number;
  created_at: string;
  configuration: {
    configuration: {
      model: string;
      epochs?: number;
      batch_size?: number;
      learning_rate?: number;
      hidden_layers?: number[];
      trees?: number;
      max_depth?: number;
    };
  };
  result: null | {
    accuracy_sample?: number;
    f1_macro_sample?: number;
    training_samples?: number;
    test_samples?: number;
    loss_curve?: number[];
    limitation?: string;
    error?: string;
    artifact_saved?: boolean;
  };
};
export function NeuralLab({
  token,
  canWrite,
}: {
  token: string;
  canWrite: boolean;
}) {
  const [model, setModel] = useState("mlp");
  const [runs, setRuns] = useState<Run[]>([]);
  const [active, setActive] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    api<Run[]>("/ml/runs", token)
      .then((data) => {
        if (live) {
          setRuns(data);
          setActive(data[0] || null);
        }
      })
      .catch((reason) => {
        if (live) setError(reason.message);
      });
    return () => {
      live = false;
    };
  }, [token]);
  const running = active?.status === "queued" || active?.status === "running";
  useEffect(() => {
    if (!active?.id || !running) return;
    let live = true;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      try {
        const data = await api<Run>(`/ml/runs/${active.id}`, token);
        if (live) {
          setActive(data);
          setRuns((old) => [
            data,
            ...old.filter((item) => item.id !== data.id),
          ]);
          if (data.status === "queued" || data.status === "running")
            timer = setTimeout(refresh, 1500);
        }
      } catch (reason) {
        if (live) {
          setError(
            reason instanceof Error
              ? reason.message
              : "No se pudo consultar el experimento",
          );
          timer = setTimeout(refresh, 5000);
        }
      }
    };
    timer = setTimeout(refresh, 700);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [active?.id, running, token]);
  async function train(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const fields = new FormData(event.currentTarget);
    const number = (key: string) => Number(fields.get(key));
    const configuration =
      model === "mlp"
        ? {
            model,
            hidden_layers: String(fields.get("layers"))
              .split(",")
              .map((value) => Number(value.trim())),
            epochs: number("epochs"),
            batch_size: number("batch"),
            learning_rate: number("learning"),
            activation: fields.get("activation"),
            optimizer: fields.get("optimizer"),
          }
        : { model, trees: number("trees"), max_depth: number("depth") };
    try {
      const result = await api<Run>("/ml/runs", token, {
        dataset_origin: "SAMPLE",
        configuration,
        samples_per_class: number("samples"),
        seed: number("seed"),
      });
      setActive(result);
      setRuns((old) => [result, ...old]);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "No se pudo entrenar",
      );
    } finally {
      setBusy(false);
    }
  }
  const loss = active?.result?.loss_curve || [];
  const maximum = Math.max(0.001, ...loss);
  const points = loss
    .map(
      (value, index) =>
        `${(index / Math.max(1, loss.length - 1)) * 600},${140 - (value / maximum) * 125}`,
    )
    .join(" ");
  return (
    <div className="lab-layout">
      <form className="panel" onSubmit={train}>
        <div className="panel-head">
          <h2>
            <BrainCircuit size={18} />
            Configuración manual
          </h2>
          <span className="badge">SAMPLE DATASET</span>
        </div>
        <p className="muted">
          El cálculo entrena un modelo real en CPU. Las etiquetas y señales son
          fixtures de laboratorio, no fallas confirmadas de vehículos.
        </p>
        <label>
          Modelo
          <select
            value={model}
            onChange={(event) => setModel(event.target.value)}
            disabled={busy || running}
          >
            <option value="mlp">Red neuronal MLP</option>
            <option value="random_forest">Random Forest · comparación</option>
          </select>
        </label>
        <div className="config-grid" key={model}>
          {model === "mlp" ? (
            <>
              <label>
                Capas ocultas (neuronas)
                <input
                  name="layers"
                  defaultValue="64,32"
                  required
                  pattern="[0-9]+(,\s*[0-9]+){0,2}"
                  title="Una a tres capas, separadas por coma. De 4 a 128 neuronas."
                />
              </label>
              <label>
                Épocas
                <input
                  name="epochs"
                  type="number"
                  min={1}
                  max={300}
                  defaultValue={60}
                  required
                />
              </label>
              <label>
                Batch size
                <input
                  name="batch"
                  type="number"
                  min={8}
                  max={256}
                  defaultValue={32}
                  required
                />
              </label>
              <label>
                Learning rate
                <input
                  name="learning"
                  type="number"
                  min={0.00001}
                  max={0.1}
                  step="any"
                  defaultValue={0.001}
                  required
                />
              </label>
              <label>
                Activación
                <select name="activation">
                  <option value="relu">ReLU</option>
                  <option value="tanh">tanh</option>
                  <option value="logistic">Sigmoide</option>
                </select>
              </label>
              <label>
                Optimizador
                <select name="optimizer">
                  <option value="adam">Adam</option>
                  <option value="sgd">SGD</option>
                </select>
              </label>
            </>
          ) : (
            <>
              <label>
                Número de árboles
                <input
                  name="trees"
                  type="number"
                  min={10}
                  max={200}
                  defaultValue={80}
                  required
                />
              </label>
              <label>
                Profundidad máxima
                <input
                  name="depth"
                  type="number"
                  min={2}
                  max={30}
                  defaultValue={8}
                  required
                />
              </label>
            </>
          )}
          <label>
            Muestras por clase
            <input
              name="samples"
              type="number"
              min={25}
              max={150}
              defaultValue={60}
              required
            />
          </label>
          <label>
            Semilla reproducible
            <input
              name="seed"
              type="number"
              min={0}
              max={2147483647}
              defaultValue={42}
              required
            />
          </label>
        </div>
        <p className="muted">
          Separación estratificada: 75% entrenamiento / 25% prueba.
          Normalización ajustada solo con entrenamiento. Límite: un trabajo a la
          vez.
        </p>
        <button disabled={busy || running || !canWrite}>
          <Play size={15} />
          {running
            ? "Entrenamiento en curso…"
            : busy
              ? "Enviando…"
              : "Entrenar con datos SAMPLE"}
        </button>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
      <div>
        <section className="panel">
          <div className="panel-head">
            <h2>Experimento seleccionado</h2>
            <span className="badge">{active?.status || "SIN EXPERIMENTO"}</span>
          </div>
          {active ? (
            <>
              <p className="mono">
                {active.id.slice(0, 8)} ·{" "}
                {active.configuration.configuration.model}
              </p>
              <p className="muted">
                Configuración del experimento:{" "}
                {active.configuration.configuration.model === "mlp"
                  ? `capas ${active.configuration.configuration.hidden_layers?.join(" / ")} · ${active.configuration.configuration.epochs} épocas · batch ${active.configuration.configuration.batch_size} · learning rate ${active.configuration.configuration.learning_rate}`
                  : `${active.configuration.configuration.trees} árboles · profundidad ${active.configuration.configuration.max_depth}`}
              </p>
              <progress
                value={active.progress}
                max={100}
                aria-label="Progreso de entrenamiento"
              />
              <p className="muted">
                {active.progress}% ·{" "}
                {new Date(active.created_at).toLocaleString("es-CO")}
              </p>
              {active.result?.accuracy_sample !== undefined && (
                <>
                  <div className="model-metrics">
                    <div>
                      <strong>
                        {(active.result.accuracy_sample * 100).toFixed(1)}%
                      </strong>
                      <span>Exactitud SAMPLE</span>
                    </div>
                    <div>
                      <strong>
                        {((active.result.f1_macro_sample || 0) * 100).toFixed(
                          1,
                        )}
                        %
                      </strong>
                      <span>F1 macro SAMPLE</span>
                    </div>
                  </div>
                  <p className="warning-copy">
                    Métrica sintética: no mide rendimiento en vehículos reales.
                  </p>
                  <p className="muted">
                    {active.result.training_samples} muestras de entrenamiento ·{" "}
                    {active.result.test_samples} de prueba
                  </p>
                </>
              )}
              {loss.length > 0 && (
                <figure className="loss-chart">
                  <svg
                    viewBox="0 0 600 150"
                    role="img"
                    aria-label="Pérdida de entrenamiento por época"
                  >
                    <path d="M0 145H600M0 0V145" stroke="#426054" fill="none" />
                    <polyline
                      points={points}
                      stroke="#6ae9c1"
                      strokeWidth="3"
                      fill="none"
                    />
                  </svg>
                  <figcaption>
                    Pérdida real del entrenamiento · {loss.length} épocas ·
                    última: {loss.at(-1)?.toFixed(4)}
                  </figcaption>
                </figure>
              )}
              {active.result?.error && (
                <p className="error" role="alert">
                  {active.result.error}
                </p>
              )}
              <p className="muted">
                {active.result?.artifact_saved
                  ? "Modelo y preprocesamiento guardados localmente."
                  : "El artefacto se guarda al finalizar."}{" "}
                Sin permiso para calibrar ni controlar máquinas.
              </p>
              <button
                className="secondary"
                onClick={() =>
                  downloadJSON(
                    active,
                    `SSScanner-experimento-${active.id}.json`,
                  )
                }
              >
                <Download size={15} />
                Exportar experimento
              </button>
            </>
          ) : (
            <p className="empty">
              Configura el primer experimento para ver resultados medidos.
            </p>
          )}
        </section>
        <section className="panel">
          <h2>Historial de modelos</h2>
          {runs.map((item) => (
            <button
              className="history-row"
              key={item.id}
              onClick={() => setActive(item)}
              disabled={running && active?.id !== item.id}
            >
              <div>
                <strong>{item.configuration.configuration.model}</strong>
                <small>
                  {item.id.slice(0, 8)} ·{" "}
                  {new Date(item.created_at).toLocaleString("es-CO")}
                </small>
              </div>
              <span>{item.status}</span>
            </button>
          ))}
        </section>
      </div>
    </div>
  );
}
