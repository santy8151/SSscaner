const state = {
  selectedView: 'summary'
};

const authView = document.getElementById('auth');
const platformView = document.getElementById('platform');
const titleEl = document.getElementById('title');
const crumbEl = document.getElementById('crumb');
const modal = document.getElementById('modal');
const modalContent = document.getElementById('modal-content');
const navButtons = Array.from(document.querySelectorAll('.nav'));
const tabs = Array.from(document.querySelectorAll('.tab'));

const viewTitles = {
  summary: 'Resumen General',
  orders: 'Pedidos',
  clients: 'Clientes',
  inventory: 'Inventario',
  warehouses: 'Almacenes',
  deliveries: 'Entregas',
  routes: 'Rutas y tracking',
  incidents: 'Incidencias',
  payments: 'Pagos'
};

function setView(viewName) {
  state.selectedView = viewName;
  titleEl.textContent = viewTitles[viewName] || 'Resumen General';
  crumbEl.textContent = 'CENTRO DE OPERACIONES LOGÍSTICAS';

  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.view === viewName);
  });
}

function bindRegisterScreen() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (authView) authView.classList.add('hidden');
    if (platformView) platformView.classList.remove('hidden');
    setView('summary');
  });
}

function bindTabs() {
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((item) => item.classList.toggle('active', item === tab));
    });
  });
}

function bindNav() {
  navButtons.forEach((button) => {
    button.addEventListener('click', () => {
      setView(button.dataset.view);
    });
  });
}

function bindDiagramModal() {
  const btn = document.getElementById('diagram-btn');
  if (!btn || !modal || !modalContent) return;

  btn.addEventListener('click', () => {
    modalContent.innerHTML = `
      <div class="modal-content-card">
        <h3>Canales de venta</h3>
        <p class="muted">Resumen del flujo comercial, canales activos y oportunidades de crecimiento por región.</p>
        <ul class="tool-list">
          <li><strong>Marketplace</strong><span>43% de volumen</span></li>
          <li><strong>Directo</strong><span>31% de volumen</span></li>
          <li><strong>Distribuidores</strong><span>26% de volumen</span></li>
        </ul>
      </div>
    `;

    modal.showModal();
  });

  const closeBtn = document.querySelector('.close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => modal.close());
  }
}

function bootstrap() {
  bindRegisterScreen();
  bindTabs();
  bindNav();
  bindDiagramModal();
  setView('summary');
}

bootstrap();