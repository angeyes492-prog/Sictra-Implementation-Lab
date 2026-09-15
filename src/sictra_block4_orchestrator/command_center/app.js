const $ = (selector, root = document) => root.querySelector(selector);
const escapeHTML = value => String(value ?? "").replace(/[&<>'"]/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[character]));

const actionCopy = {
  PAUSE: ["Pausar procesamiento", "La ruta local no progresará hasta que se reanude."],
  RESUME: ["Reanudar procesamiento", "La próxima operación local podrá avanzar la ruta retenida."],
  STOP: ["Detener runtime local", "El runtime fallará cerrado hasta que un operador lo inicie de nuevo."],
  START: ["Iniciar runtime local", "El inicio no reproduce ni aprueba trabajo automáticamente."],
  RETRY_CASE: ["Reintentar caso", "Se reutilizará exactamente el paquete retenido y su límite de reintentos."],
  VERIFY_JOURNAL: ["Verificar journal", "Se comprobará la integridad HMAC sin modificar el runtime."],
};

const routeLabels = {
  BLOCK1: ["01", "Evidencia retenida"],
  BLOCK2: ["02", "Candidato de diseño"],
  BLOCK3: ["03", "Señal gobernada"],
  HUMAN: ["04", "Revisión humana"],
};

let cases = [];
let selectedCaseId = null;
let selectedEvents = [];
let control = null;
let pendingAction = null;

function humanize(value) {
  return String(value || "—").replaceAll("_", " ");
}

function formatTime(value) {
  if (!value) return "sin registro";
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) return escapeHTML(value);
  return new Intl.DateTimeFormat("es-HN", {day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit"}).format(timestamp);
}

function stateClass(value) {
  if (value === "STOPPED" || value === "RETURN_UPSTREAM" || value === "REJECTED") return "is-danger";
  if (value === "PAUSED" || value === "HUMAN_REVIEW_REQUIRED") return "is-review";
  return "is-current";
}

function selectedCase() {
  return cases.find(item => item.case_id === selectedCaseId) || null;
}

function routeProgress(item) {
  if (!item) return "—";
  const humanGate = item.state === "HUMAN_REVIEW_REQUIRED" ? 1 : 0;
  return `${Math.min(item.lineage.length + humanGate, 4)}/4`;
}

function renderTop() {
  const state = control?.state || "UNAVAILABLE";
  $("#top-control-state").textContent = `Runtime · ${humanize(state)}`;
  $("#top-control-state").className = `state-pill ${stateClass(state)}`;
  $("#runtime-state").textContent = control ? `JOURNAL · ${humanize(state)}` : "LECTURA DETENIDA";
  $("#atlas-note span:last-child").textContent = control
    ? `Journal local verificado · ${cases.length} caso${cases.length === 1 ? "" : "s"} observable${cases.length === 1 ? "" : "s"}.`
    : "La lectura local se detuvo antes de mostrar un estado no verificado.";
}

function renderRoute(item) {
  const title = $("#route-title");
  const state = $("#route-state");
  const lattice = $("#route-lattice");
  const caption = $("#route-caption");
  if (!item) {
    title.textContent = "Sin caso seleccionado";
    state.textContent = "—";
    state.className = "route-state";
    lattice.innerHTML = "";
    caption.textContent = "Elige un caso de la cola para inspeccionar su linaje verificable.";
    return;
  }
  title.textContent = item.case_id;
  state.textContent = humanize(item.state);
  state.className = `route-state ${stateClass(item.state)}`;
  const lineage = new Set(item.lineage);
  const stages = ["BLOCK1", "BLOCK2", "BLOCK3", "HUMAN"];
  lattice.innerHTML = stages.map((stage, index) => {
    const passed = lineage.has(stage);
    const current = stage === "HUMAN" && item.state === "HUMAN_REVIEW_REQUIRED";
    const returned = item.state === "RETURN_UPSTREAM" && index === 0;
    const marker = current ? "is-current" : returned ? "is-danger" : passed ? "is-passed" : "";
    const [number, label] = routeLabels[stage];
    return `<li class="${marker}"><span class="route-number">${number}</span><span>${label}</span><i aria-hidden="true"></i></li>`;
  }).join("");
  caption.textContent = item.state === "HUMAN_REVIEW_REQUIRED"
    ? "La autonomía local se detuvo en la frontera de revisión humana."
    : `Checkpoint observado: ${humanize(item.state)}. No se infiere ejecución de otro bloque.`;
}

function renderReadouts(item) {
  $("#case-count").textContent = String(cases.length);
  $("#review-count").textContent = String(cases.filter(candidate => candidate.state === "HUMAN_REVIEW_REQUIRED").length);
  $("#route-count").textContent = routeProgress(item);
}

function renderCases() {
  const list = $("#case-list");
  if (!cases.length) {
    list.innerHTML = `<div class="empty-state"><b>No hay paquetes controlados</b><p>Un operador debe retener e ingresar un paquete local firmado antes de que exista una ruta observable.</p></div>`;
    return;
  }
  list.innerHTML = cases.map(item => `<button class="case-row ${item.case_id === selectedCaseId ? "selected" : ""}" type="button" data-case-id="${escapeHTML(item.case_id)}" aria-pressed="${item.case_id === selectedCaseId}">
    <span class="case-node ${stateClass(item.state)}" aria-hidden="true"></span>
    <span class="case-summary"><b>${escapeHTML(item.case_id)}</b><small>${escapeHTML(item.run_id)} · ${escapeHTML(item.lineage.join(" → "))}</small></span>
    <span class="case-meta"><small>${formatTime(item.expires_at)}</small><strong class="case-state ${stateClass(item.state)}">${escapeHTML(humanize(item.state))}</strong></span>
  </button>`).join("");
  document.querySelectorAll("[data-case-id]").forEach(button => button.addEventListener("click", async () => {
    selectedCaseId = button.dataset.caseId;
    selectedEvents = await loadEvents(selectedCaseId);
    render();
  }));
}

function renderInspector(item) {
  const title = $("#inspector-title");
  const detail = $("#case-detail");
  if (!item) {
    title.textContent = "Selecciona un caso";
    detail.innerHTML = "<p>La procedencia, restricciones y checkpoint aparecerán aquí sin reinterpretar su contenido.</p>";
    return;
  }
  title.textContent = item.case_id;
  const canRetry = control?.state === "RUNNING" && ["RETURN_UPSTREAM", "REJECTED"].includes(item.state);
  detail.innerHTML = `<p class="inspector-lede">Estado retenido en el journal local. La interfaz no lo convierte en aceptación.</p>
    <dl>
      <div><dt>Estado</dt><dd>${escapeHTML(humanize(item.state))}</dd></div>
      <div><dt>Certeza</dt><dd>${escapeHTML(item.certainty)}</dd></div>
      <div><dt>Disposición</dt><dd>${escapeHTML(humanize(item.disposition))}</dd></div>
      <div><dt>Reintentos</dt><dd>${escapeHTML(item.retry_count)} / 3</dd></div>
      <div><dt>Fuente</dt><dd title="${escapeHTML(item.source_hash)}">${escapeHTML(item.source_hash.slice(0, 18))}…</dd></div>
      <div><dt>Raíz</dt><dd title="${escapeHTML(item.provenance_root)}">${escapeHTML(item.provenance_root)}</dd></div>
    </dl>
    <div class="restriction-list"><b>Restricciones</b>${item.restrictions.map(restriction => `<span>${escapeHTML(humanize(restriction))}</span>`).join("")}</div>
    ${canRetry ? `<button type="button" class="button button-outline" data-control-action="RETRY_CASE">Reintentar caso retenido</button>` : ""}`;
  detail.querySelector("[data-control-action]")?.addEventListener("click", () => queueAction("RETRY_CASE"));
}

function renderEvents() {
  const list = $("#event-list");
  if (!selectedCaseId) {
    list.innerHTML = '<li class="empty-event">No hay un caso seleccionado.</li>';
    return;
  }
  if (!selectedEvents.length) {
    list.innerHTML = '<li class="empty-event">El journal no devolvió eventos para este caso.</li>';
    return;
  }
  list.innerHTML = selectedEvents.map(event => `<li><span class="event-dot ${stateClass(event.state)}" aria-hidden="true"></span><div><b>${escapeHTML(humanize(event.event_type))}</b><p>${escapeHTML(humanize(event.state))} · ${formatTime(event.created_at)}</p></div></li>`).join("");
}

function renderControls() {
  const status = control?.state || "UNAVAILABLE";
  const led = $("#control-led");
  led.className = `control-led ${stateClass(status)}`;
  $("#control-status").textContent = control
    ? `${humanize(status)} · ${control.changed_at ? `cambió ${formatTime(control.changed_at)}` : "estado inicial del journal"}`
    : "No se puede confirmar la disponibilidad del runtime local.";
  const actions = control?.available_actions || [];
  $("#control-actions").innerHTML = actions.map(action => `<button type="button" class="control-action ${action === "STOP" ? "is-stop" : ""}" data-control-action="${action}">${escapeHTML(actionCopy[action][0])}<small>${escapeHTML(actionCopy[action][1])}</small></button>`).join("") || '<p class="control-unavailable">No hay acciones disponibles mientras el journal no sea verificable.</p>';
  document.querySelectorAll("[data-control-action]").forEach(button => button.addEventListener("click", () => queueAction(button.dataset.controlAction)));
  const confirmation = $("#control-confirmation");
  confirmation.hidden = !pendingAction;
  if (pendingAction) {
    $("#control-confirmation-copy").textContent = `Confirmar: ${actionCopy[pendingAction][0]}. Esta acción no publica ni entrega contenido.`;
  }
}

function render() {
  const item = selectedCase();
  renderTop();
  renderRoute(item);
  renderReadouts(item);
  renderCases();
  renderInspector(item);
  renderEvents();
  renderControls();
}

function createRequestId(action) {
  const suffix = globalThis.crypto?.randomUUID?.().replaceAll("-", "") || `${Date.now()}${Math.random().toString(36).slice(2)}`;
  return `cc-${action.toLowerCase()}-${suffix}`.slice(0, 96);
}

function queueAction(action) {
  if (action === "VERIFY_JOURNAL") {
    executeAction(action);
    return;
  }
  if (action === "RETRY_CASE" && !selectedCase()) {
    $("#control-result").textContent = "Selecciona primero un caso retornado antes de reintentar.";
    return;
  }
  pendingAction = action;
  renderControls();
  $("#confirm-control").focus();
}

async function executeAction(action) {
  const payload = {action};
  if (action !== "VERIFY_JOURNAL") {
    payload.request_id = createRequestId(action);
    payload.reason = $("#control-reason").value;
    if (action === "RETRY_CASE") payload.case_id = selectedCaseId;
  }
  $("#control-result").textContent = `${actionCopy[action][0]} en curso…`;
  try {
    const response = await fetch("/api/controls", {method:"POST", credentials:"same-origin", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "CONTROL_UNAVAILABLE");
    pendingAction = null;
    $("#control-result").textContent = result.receipt?.replayed ? "Solicitud repetida: se conservó su recibo original." : `${actionCopy[action][0]} completado dentro del runtime local.`;
    await load();
  } catch (error) {
    pendingAction = null;
    $("#control-result").textContent = `Acción rechazada: ${error.message}`;
    renderControls();
  }
}

async function loadEvents(caseId) {
  if (!caseId) return [];
  try {
    const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}/events`, {credentials:"same-origin"});
    if (!response.ok) throw new Error("EVENTS_UNAVAILABLE");
    return (await response.json()).events || [];
  } catch (_) {
    return [];
  }
}

async function load() {
  try {
    const response = await fetch("/api/cases", {credentials:"same-origin"});
    if (!response.ok) throw new Error("JOURNAL_UNAVAILABLE");
    const payload = await response.json();
    cases = payload.cases || [];
    control = payload.control || null;
    if (!selectedCaseId || !cases.some(item => item.case_id === selectedCaseId)) selectedCaseId = cases[0]?.case_id || null;
    selectedEvents = await loadEvents(selectedCaseId);
    render();
  } catch (_) {
    control = null;
    cases = [];
    selectedEvents = [];
    $("#runtime-state").textContent = "LECTURA DETENIDA";
    $("#case-list").innerHTML = '<div class="empty-state"><b>Journal no disponible</b><p>Verifica la integridad local antes de intentar cualquier control.</p></div>';
    render();
  }
}

$("#confirm-control").addEventListener("click", () => pendingAction && executeAction(pendingAction));
$("#cancel-control").addEventListener("click", () => { pendingAction = null; $("#control-result").textContent = "Acción cancelada antes de cambiar el runtime."; renderControls(); });
load();
