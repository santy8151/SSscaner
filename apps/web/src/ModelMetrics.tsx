export function ModelMetrics({
  result,
}: {
  result: Record<string, unknown> | null;
}) {
  if (!result) return <p>El experimento todavía no tiene resultados.</p>;
  const rows: [string, string][] = [];
  const percent = (v: unknown) => `${(Number(v) * 100).toFixed(1)}%`;
  if (typeof result.accuracy_sample === "number")
    rows.push(
      ["Exactitud SAMPLE", percent(result.accuracy_sample)],
      ["F1 macro SAMPLE", percent(result.f1_macro_sample)],
    );
  if (Array.isArray(result.test_cluster_counts))
    rows.push(["Muestras por grupo", result.test_cluster_counts.join(" / ")]);
  if (Array.isArray(result.explained_variance_ratio))
    rows.push([
      "Varianza explicada por eje",
      result.explained_variance_ratio.map(percent).join(" / "),
    ]);
  if (typeof result.test_reconstruction_mse === "number")
    rows.push([
      "Error de reconstrucción",
      result.test_reconstruction_mse.toFixed(4),
    ]);
  if (typeof result.test_outlier_fraction === "number")
    rows.push(["Atípicos en prueba", percent(result.test_outlier_fraction)]);
  if (typeof result.training_samples === "number")
    rows.push(
      ["Muestras de entrenamiento", String(result.training_samples)],
      ["Muestras de prueba", String(result.test_samples)],
    );
  return (
    <>
      <div className="model-metrics">
        {rows.map(([label, value]) => (
          <div key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <p>
        {result.error
          ? String(result.error)
          : "Resultados de datos sintéticos. No miden precisión en vehículos reales."}
      </p>
    </>
  );
}
