# Verificación · primera fase · 2026-09-07

## Actualización BETA 0.3 · 2026-09-08

- **35 pruebas Python aprobadas**; dos advertencias de dependencias TestClient/AnyIO. Ruff, ESLint, TypeScript y Vite aprobados. Bundle actual ~184 kB / 59 kB gzip.
- Prueba navegador/API con fixture BLE: trama `5e01` guardada como 35 psi_g CLIENT_BLE; desconexión y denegación de permiso no generan respaldo ficticio. Esta prueba no utiliza hardware físico.
- Entrenamiento de Random Forest y exportación comprobados desde UI; cinco métodos ejecutados en pruebas del backend. K-Means/PCA/Isolation Forest no reportan exactitud diagnóstica.
- Señal SAMPLE de 62.5 Hz reconocida por la API desde UI; modelo de visión con URL ajena rechazado y cámara deshabilitada. No se ha validado inferencia con un modelo real del usuario.
- Instrumentos y Redes neuronales: navegador sin errores JavaScript, sin desbordamiento horizontal a 390 px. Rutas antiguas bloqueadas en servidor.
- Evidencia actual: `artifacts/verify-beta-ui.cjs`, `artifacts/studio-mobile.png`, `artifacts/investor-instruments.png`, `artifacts/investor-neural.png`.

La tabla siguiente conserva la evidencia histórica de las fases anteriores; sus rutas no representan la navegación actual.

## Evidencia ejecutada

| Comprobación | Resultado |
|---|---|
| Instalación Python en .venv | OK; requirements-mvp.lock generado; pip check sin conflictos |
| Instalación web | OK; package-lock.json; auditoría npm informó 0 vulnerabilidades al instalar |
| pytest tests/mvp | **30 passed** después de la ampliación BETA; 2 advertencias de deprecación en dependencias de TestClient/AnyIO |
| Ruff lint y formato | OK |
| ESLint + TypeScript | OK |
| Vite build | OK; bundle JS BETA ~196 kB / ~61 kB gzip |
| Arranque FastAPI | OK, 127.0.0.1:8000, SQLite local |
| /health y /ready | OK, proceso y esquema accesibles |
| Navegador escritorio | Registro de empresa → equipo → escenario → captura → diagnóstico/calibración → historial |
| Login tras recargar | OK; equipo e historial conservados en base de datos |
| Navegador móvil | 390×844, sin desbordamiento horizontal; botón de logout disponible |
| Errores de página | agent-browser no reportó errores; sin overlay de Vite |
| Video MP4 | 24.0 s, 1080×1920, 24 fps, H.264/yuv420p + AAC |
| Decodificación video/audio | FFmpeg decodificó todo el archivo sin errores; revisados fotogramas en 2/14/21 s |

Las pruebas cubren hash/expiración/revocación de sesiones, roles, denegación entre empresas, persistencia después de reinicio, unidades/timestamps/números finitos, duplicados y conflictos de ingestión, ocho escenarios, límite de peticiones/cuerpo y rechazo de parámetros críticos no previstos en Calibration. La ampliación verifica endian/escala/referencia de presión, tramas truncadas/NaN, separación CLIENT_BLE/SAMPLE, jobs y artefactos reales de MLP/Random Forest sobre fixtures, parámetros limitados y privacidad de experimentos. No existe ejecución de máquinas ni inferencia validada de averías.

## Límites explícitos

- Docker no está instalado en este equipo. PostgreSQL, construcción de contenedor y Compose **no ejecutados**; DDL PostgreSQL exportado para revisión, no equivale a ejecución en ese motor.
- No se probaron dispositivos físicos, CAN/J1939/OBD reales ni máquinas de refrigerante. Los nombres de protocolos del simulador son metadatos.
- No hay fuentes OEM ni modelo validado. SOURCE_REQUIRED es el resultado esperado.
- La suite heredada no forma parte de estos 30 tests. Sus errores de arquitectura/importación se documentan en ARCHITECTURE.md; no se presenta como funcional.

La descarga de sesión fue cancelada por agent-browser; se verificó con Playwright en Edge, con descarga aceptada, JSON parseado y una captura SAMPLE persistida. No se requirió modificar la función de descarga para esa comprobación.
- No hay migraciones incrementales, RLS, operación multiworker, backup/restauración ejecutada ni endurecimiento para producción.
- El video es una pieza conceptual del laboratorio BETA con música sintetizada, no una demostración de hardware real. No se publicó en plataformas externas.

## Artefactos de revisión

`artifacts/dashboard.png`, `artifacts/mobile-final.png`, `promo/SSScanner-promo-vertical.mp4`, `promo/verified-frame-2.png`, `promo/verified-frame-14.png`, `promo/verified-frame-21.png`. La cuenta de demostración local está en LOCAL_ACCESS.md, excluido de Git junto con la base local.
