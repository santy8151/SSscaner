const rows = document.querySelector('#rows');
const error = document.querySelector('#error');
const exportButton = document.querySelector('#export');
let report = null;
let sequence = 0;
function addRow() {
  const row = document.createElement('tr');
  const id = ++sequence;
  for (const [field, title, type] of [['name','Nombre de medición','text'], ['value','Valor medido','number'], ['unit','Unidad','text'], ['minimum','Mínimo de referencia','number'], ['maximum','Máximo de referencia','number']]) {
    const cell = document.createElement('td');
    const input = document.createElement('input');
    input.type = type;
    input.dataset.field = field;
    input.setAttribute('aria-label', `${title}, fila ${id}`);
    input.required = true;
    if (type === 'number') input.step = 'any';
    else input.maxLength = field === 'unit' ? 30 : 80;
    cell.append(input); row.append(cell);
  }
  const cell = document.createElement('td');
  const remove = document.createElement('button');
  remove.type = 'button'; remove.className = 'secondary'; remove.textContent = '×';
  remove.setAttribute('aria-label', `Eliminar medición ${id}`);
  remove.onclick = () => { row.remove(); invalidate(); };
  cell.append(remove); row.append(cell); rows.append(row);
}
function invalidate() {
  report = null;
  exportButton.disabled = true;
  document.querySelector('#result').textContent = 'Mediciones modificadas. Compara de nuevo para actualizar el informe.';
}
document.querySelector('#add-row').onclick = () => { if (rows.children.length < 100) { addRow(); invalidate(); } };
document.querySelector('#measurement-form').addEventListener('input', invalidate);
document.querySelector('#measurement-form').addEventListener('submit', async (event) => {
  event.preventDefault(); error.textContent = ''; report = null; exportButton.disabled = true;
  const submit = document.querySelector('#submit');
  const payload = {vehicle: document.querySelector('#vehicle').value.trim(), source: document.querySelector('#source').value, readings: Object.create(null), references: Object.create(null)};
  try {
    if (!rows.children.length) throw new Error('Añade al menos una medición.');
    if (!payload.vehicle) throw new Error('Identifica el vehículo.');
    for (const row of rows.children) {
      const fields = Object.fromEntries([...row.querySelectorAll('input')].map(input => [input.dataset.field, input.value.trim()]));
      if (!fields.name || !fields.unit) throw new Error('Completa el nombre y la unidad de cada medición.');
      if (Object.hasOwn(payload.readings, fields.name)) throw new Error('Usa nombres distintos para cada medición.');
      const value = Number(fields.value), minimum = Number(fields.minimum), maximum = Number(fields.maximum);
      if (![value,minimum,maximum].every(Number.isFinite) || minimum > maximum) throw new Error('Revisa los números y el orden de los rangos.');
      payload.readings[fields.name] = value;
      payload.references[fields.name] = {minimum, maximum, unit: fields.unit};
    }
    submit.disabled = true; submit.textContent = 'Comparando…';
    const response = await fetch('/api/diagnostics', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error(`No se pudo comparar (${response.status}). Revisa las mediciones.`);
    const data = await response.json();
    report = data;
    const result = document.querySelector('#result'); result.className = ''; result.replaceChildren();
    const meta = document.createElement('p'); meta.className = 'result-meta'; meta.textContent = `${data.vehicle} · ${new Date(data.timestamp).toLocaleString('es-CO')}`; result.append(meta);
    const labels = {within_range:'Dentro del rango',above_range:'Sobre el rango',below_range:'Bajo el rango',reference_required:'Sin referencia'};
    for (const reading of data.results) {
      const line = document.createElement('div'); line.className = 'result-row' + (['above_range','below_range'].includes(reading.status) ? ' outside' : '');
      const name = document.createElement('span'); name.textContent = `${reading.name}: ${reading.value} ${reading.reference?.unit || ''}`;
      const state = document.createElement('strong'); state.textContent = labels[reading.status];
      line.append(name,state); result.append(line);
    }
    const note = document.createElement('p'); note.className = 'report-note'; note.textContent = `${data.finding} ${data.recommendation}`; result.append(note);
    exportButton.disabled = false;
  } catch (failure) { error.textContent = failure.message; document.querySelector('#result').textContent = 'No hay un informe actualizado.'; }
  finally { submit.disabled = false; submit.textContent = 'Comparar mediciones ↗'; }
});
exportButton.onclick = () => {
  if (!report) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
  const link = document.createElement('a'); link.href=url; link.download='ssscaner-informe.json'; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
};
fetch('/health', {signal:AbortSignal.timeout(5000)}).then(response => {if(!response.ok) throw new Error(); return response.json();}).then(()=>{document.querySelector('#api-status').textContent='● API DISPONIBLE · ENTRADA MANUAL';}).catch(()=>{document.querySelector('#api-status').textContent='API NO DISPONIBLE';});
addRow();
