# Laboratorio de modelos BETA

Entrenamiento real con scikit-learn, separado del Diagnosis Engine y de Calibration. Dataset `synthetic-fixtures-v1`: siete escenarios SAMPLE con ruido reproducible; no contiene casos reales confirmados. El contrato rechaza origen REAL.

MLP: 1–3 capas, 4–128 neuronas/capa; ReLU/tanh/sigmoide; Adam/SGD; 1–300 épocas; batch 8–256 (debe caber en train); learning rate 0.00001–0.1. Cada llamada partial_fit hace una época y registra pérdida. No se afirma convergencia por agotar épocas.

Random Forest: 10–200 árboles y profundidad 2–30; no se muestran batch/learning rate porque no aplican a ese modelo. CPU limitada a un hilo y un entrenamiento global concurrente en este prototipo.

Partición estratificada 75/25 con semilla. Imputación/indicadores de ausencia y escalado se ajustan solo en train. Se guardan matriz de confusión, exactitud/F1 SAMPLE, tamaños, hash del dataset, configuración y curva de pérdida cuando corresponde. No se interpreta exactitud de fixtures como probabilidad de avería o validación OEM.

`model_runs`: tenant, autor, configuración, estado, progreso, resultado y fecha. El artefacto joblib se guarda en `data/local/models/{organization_id}/{run_id}.joblib` con modelo y preprocesamiento. No se aceptan archivos pickle/joblib subidos por clientes. No cargar artefactos de origen desconocido.

Worker local de una plaza; un segundo entrenamiento simultáneo devuelve 429. Reinicio marca trabajos sin finalizar como `interrupted`. No hay cola distribuida, cancelación remota ni servicio de inferencia sobre vehículos reales. No usar múltiples procesos contra este worker sin rediseñar coordinación.

API: POST /api/v1/ml/runs → 202; GET /api/v1/ml/runs; GET /api/v1/ml/runs/{id}. Requiere rol technician/admin para crear y tenant para consultar. Frontend consulta progreso sin bloquear el navegador y exporta JSON del experimento.

Fuente primaria: [MLPClassifier de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html).
# Actualización 0.3

El laboratorio vigente está descrito en [BETA-03](../BETA-03.md): cinco métodos y selección de características por componente, disponibles en `/models`. La descripción de dos modelos que sigue corresponde a la primera ampliación. Visión se carga como modelo externo de Teachable Machine en el iframe de Instrumentos; no hay dataset ni modelo de luces incluido.
