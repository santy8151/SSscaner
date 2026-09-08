/* Inference only. No camera frame upload, vehicle commands or fallback labels. */
const byId = (id) => document.getElementById(id);
let model = null,
  stream = null,
  running = false,
  generation = 0,
  photoURL = null;
const status = (text) => {
  byId("status").textContent = text;
};
function script(src) {
  return new Promise((resolve, reject) => {
    const tag = document.createElement("script");
    tag.src = src;
    tag.onload = resolve;
    tag.onerror = () => {
      tag.remove();
      reject(new Error("No se pudo descargar la librería de visión"));
    };
    document.head.append(tag);
  });
}
function stop() {
  running = false;
  generation++;
  stream?.getTracks().forEach((t) => t.stop());
  stream = null;
  byId("video").srcObject = null;
  byId("video").hidden = true;
  byId("stop").disabled = true;
  byId("camera").disabled = !model;
}
function results(rows) {
  byId("results").replaceChildren();
  for (const row of rows.sort((a, b) => b.probability - a.probability)) {
    const item = document.createElement("div"),
      bar = document.createElement("progress");
    item.textContent = `${row.className}: ${(row.probability * 100).toFixed(1)}%`;
    bar.max = 1;
    bar.value = row.probability;
    item.append(bar);
    byId("results").append(item);
  }
}
byId("load").onclick = async () => {
  stop();
  byId("load").disabled = true;
  byId("file").disabled = true;
  model?.dispose?.();
  model = null;
  byId("camera").disabled = true;
  byId("results").replaceChildren();
  try {
    const url = new URL(byId("url").value);
    if (
      url.origin !== "https://teachablemachine.withgoogle.com" ||
      !/^\/models\/[A-Za-z0-9_-]+\/?$/.test(url.pathname) ||
      url.search ||
      url.hash
    )
      throw new Error(
        "Usa el enlace HTTPS de exportación de Teachable Machine /models/ID/",
      );
    status("Descargando modelo…");
    if (!window.tf)
      await script(
        "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js",
      );
    if (!window.tmImage)
      await script(
        "https://cdn.jsdelivr.net/npm/@teachablemachine/image@0.8.5/dist/teachablemachine-image.min.js",
      );
    const base = url.href.replace(/\/?$/, "/");
    model = await window.tmImage.load(
      base + "model.json",
      base + "metadata.json",
    );
    byId("camera").disabled = false;
    byId("file").disabled = false;
    status(
      `Modelo cargado · ${model.getTotalClasses()} clases. Selecciona una imagen o inicia la cámara.`,
    );
  } catch (e) {
    status(e.message);
  } finally {
    byId("load").disabled = false;
  }
};
byId("camera").onclick = async () => {
  stop();
  const run = generation;
  byId("camera").disabled = true;
  try {
    const media = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240 },
      audio: false,
    });
    if (run !== generation) {
      media.getTracks().forEach((t) => t.stop());
      return;
    }
    stream = media;
    const video = byId("video");
    video.srcObject = stream;
    video.hidden = false;
    byId("photo").hidden = true;
    await video.play();
    running = true;
    byId("stop").disabled = false;
    status("Cámara activa · inferencia local");
    while (running && run === generation) {
      const rows = await model.predict(video);
      if (running && run === generation) results(rows);
      await new Promise((r) => setTimeout(r, 250));
    }
  } catch (e) {
    stop();
    status("No se pudo usar la cámara: " + e.message);
  }
};
byId("stop").onclick = () => {
  stop();
  status("Cámara detenida");
};
byId("file").onchange = async (e) => {
  stop();
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > 10000000) {
    status("Imagen máxima: 10 MB");
    return;
  }
  if (photoURL) URL.revokeObjectURL(photoURL);
  photoURL = URL.createObjectURL(file);
  const photo = byId("photo");
  photo.src = photoURL;
  try {
    await photo.decode();
    photo.hidden = false;
    results(await model.predict(photo));
    status("Imagen local analizada");
  } catch (e) {
    status("No se pudo analizar: " + e.message);
  }
};
window.addEventListener("pagehide", stop);
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stop();
    status("Cámara detenida al ocultar la pestaña");
  }
});
