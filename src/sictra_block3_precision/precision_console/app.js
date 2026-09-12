"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[character]));

const views = {
  accounts: {
    name: "Cuentas",
    heading: "#accounts-heading",
    guidance: "Ubica la cuenta y su evidencia",
    copy: "La identidad aprobada delimita la revisión; no demuestra por sí sola una oportunidad comercial.",
    next: "Comprueba el host oficial y las limitaciones del dossier.",
    route: "accounts",
  },
  admission: {
    name: "Admisión",
    heading: "#admission-heading",
    guidance: "Comprueba la frontera de ingreso",
    copy: "Issuer, política, atestación y vigencia deben coincidir antes de que el contexto produzca una señal.",
    next: "Si la disposición permite continuar, revisa las señales; si no, devuelve el contexto al origen.",
    route: "admission",
  },
  signals: {
    name: "Señales",
    heading: "#signals-heading",
    guidance: "Separa señales de hipótesis",
    copy: "Una señal gobernada sigue siendo candidata; una hipótesis conserva incertidumbre y requiere revisión.",
    next: "Contrasta cada señal con su estado antes de tomar una decisión humana.",
    route: "signals",
  },
  control: {
    name: "Control",
    heading: "#control-heading",
    guidance: "Reconoce límites y abstenciones",
    copy: "Una prohibición o un retorno upstream puede ser el comportamiento correcto del sistema.",
    next: "Confirma que las acciones prohibidas sigan bloqueadas y registra la revisión humana.",
    route: "control",
  },
};

let data = null;
let activeView = "accounts";

function card(label, value, detail = "", className = "") {
  return `<article class="card ${esc(className)}"><span>${esc(label)}</span><strong>${esc(value)}</strong>${detail ? `<small>${esc(detail)}</small>` : ""}</article>`;
}

function emptyState(title, next) {
  return `<div class="empty-state"><strong>${esc(title)}</strong><span>${esc(next)}</span></div>`;
}

async function getJSON(path) {
  const response = await fetch(path);
  let payload;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error(`respuesta local no interpretable (${response.status})`);
  }
  if (!response.ok) throw new Error(payload.error || `Error HTTP ${response.status}`);
  return payload;
}

function setView(view, { focus = false } = {}) {
  activeView = view;
  const profile = views[view];
  $$('[data-view]').forEach((button) => {
    const current = button.dataset.view === view;
    button.classList.toggle("active", current);
    if (current) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  $$('[data-panel]').forEach((panel) => {
    const current = panel.dataset.panel === view;
    panel.classList.toggle("active", current);
    panel.hidden = !current;
  });
  $$(".route-step").forEach((step) => {
    const current = step.dataset.route === profile.route;
    step.classList.toggle("current", current);
    if (current) step.setAttribute("aria-current", "step");
    else step.removeAttribute("aria-current");
  });
  $("#view-name").textContent = profile.name;
  $("#view-guidance-title").textContent = profile.guidance;
  $("#view-guidance-copy").textContent = profile.copy;
  $("#view-next-step").textContent = profile.next;
  if (focus) $(profile.heading)?.focus();
}

function renderContext() {
  $("#context-tenant").textContent = data.account.tenant_id;
  $("#context-account").textContent = data.account.account_id;
  $("#context-evidence").textContent = data.fixture;
  $("#context-disposition").textContent = data.admission.disposition;
}

function renderAccounts() {
  const account = data.account;
  const dossier = data.dossier;
  const limitations = dossier.limitations.length
    ? `<ul>${dossier.limitations.map((value) => `<li>${esc(value)}</li>`).join("")}</ul>`
    : emptyState("Sin limitaciones declaradas", "Devuelve el dossier al origen; la ausencia de límites no equivale a libertad de uso.");
  $("#account-grid").innerHTML =
    card("Cuenta", account.account_id, account.tenant_id) +
    card("Dominio oficial", account.official_host, account.purpose) +
    card("Dossier", dossier.dossier_id, dossier.state) +
    card("Observaciones", dossier.observations, `${dossier.quarantined} en cuarentena`) +
    `<article class="card wide"><span>Limitaciones</span>${limitations}<code>${esc(dossier.fingerprint)}</code></article>`;
}

function renderAdmission() {
  const admission = data.admission;
  const continuing = admission.disposition === "CONTINUE";
  const reasons = admission.reasons.length ? admission.reasons.join(", ") : "SIN_BLOQUEOS_DECLARADOS";
  const next = continuing
    ? "Revisar señales candidatas; CONTINUE no significa aceptación."
    : "Devolver el contexto al origen y reparar los códigos indicados.";
  $("#admission-card").innerHTML = `<article class="admission ${continuing ? "pass" : "return"}">
    <div><span>Disposición</span><strong>${esc(admission.disposition)}</strong><div class="next-action"><span>Siguiente paso</span><strong>${esc(next)}</strong></div></div>
    <dl><dt>Issuer</dt><dd>${esc(admission.issuer_id)}</dd><dt>Policy</dt><dd>${esc(admission.policy_id)}</dd><dt>Atestación</dt><dd>${esc(admission.attestation)}</dd><dt>Evidencia</dt><dd>${esc(admission.evidence_state)}</dd><dt>Razones</dt><dd>${esc(reasons)}</dd></dl>
  </article>`;
}

function signalGroup(title, code, signals) {
  const content = signals.length
    ? `<div class="cards">${signals.map((signal) => card(`${signal.kind} · ${signal.dimension}`, signal.value, signal.state, "review")).join("")}</div>`
    : emptyState(`Sin ${title.toLowerCase()}`, "No se infiere una conclusión. Revisa la admisión y la evidencia upstream.");
  return `<section class="semantic-group"><header><h3>${esc(title)}</h3><span>${esc(code)}</span></header>${content}</section>`;
}

function renderSignals() {
  if (!data.signals.length) {
    $("#signals-list").innerHTML = emptyState("Sin señales gobernadas", "No hay base para una decisión. Revisa admisión y procedencia; ninguna señal fue aceptada.");
    return;
  }
  const hypotheses = data.signals.filter((signal) => signal.kind === "HYPOTHESIS");
  const governed = data.signals.filter((signal) => signal.kind !== "HYPOTHESIS");
  $("#signals-list").innerHTML = signalGroup("Hipótesis", "REVIEW_REQUIRED", hypotheses) + signalGroup("Señales gobernadas", "CANDIDATE_NOT_ACCEPTED", governed);
}

function controlGroup(title, code, controls, className) {
  const content = controls.length
    ? `<div class="cards">${controls.map((control) => card(control.name, control.state, "", className)).join("")}</div>`
    : emptyState(`Sin ${title.toLowerCase()}`, "No asumas un PASS; revisa el contrato y la evidencia local.");
  return `<section class="semantic-group"><header><h3>${esc(title)}</h3><span>${esc(code)}</span></header>${content}</section>`;
}

function renderControls() {
  if (!data.controls.length) {
    $("#controls-list").innerHTML = emptyState("Sin controles declarados", "El estado es INSUFFICIENT EVIDENCE; ninguna acción queda habilitada.");
    return;
  }
  const prohibited = data.controls.filter((control) => control.state === "PROHIBITED");
  const review = data.controls.filter((control) => control.state === "REQUIRED");
  const integrity = data.controls.filter((control) => !["PROHIBITED", "REQUIRED"].includes(control.state));
  $("#controls-list").innerHTML =
    controlGroup("Integridad", "LOCAL_BOUNDARY", integrity, "integrity") +
    controlGroup("Revisión", "HUMAN_REQUIRED", review, "review") +
    controlGroup("Acciones prohibidas", "PROHIBITED", prohibited, "prohibited");
}

function render() {
  renderContext();
  renderAccounts();
  renderAdmission();
  renderSignals();
  renderControls();
  setView(activeView);
}

function clearWorkspace() {
  data = null;
  $("#context-tenant").textContent = "Lectura descartada";
  $("#context-account").textContent = "Lectura descartada";
  $("#context-evidence").textContent = "INSUFFICIENT EVIDENCE";
  $("#context-disposition").textContent = "RETURN_UPSTREAM";
  for (const selector of ["#account-grid", "#admission-card", "#signals-list", "#controls-list"]) $(selector).replaceChildren();
  $$('[data-panel]').forEach((panel) => { panel.hidden = true; panel.classList.remove("active"); });
}

async function load() {
  const main = $("#workspace");
  const loading = $("#loading");
  const error = $("#error");
  const refresh = $("#refresh");
  const retry = $("#retry");
  const status = $("#refresh-status");
  main.setAttribute("aria-busy", "true");
  main.dataset.evidenceState = "loading";
  refresh.disabled = true;
  retry.disabled = true;
  loading.hidden = false;
  error.hidden = true;
  status.textContent = "Actualizando evidencia local…";
  try {
    const payload = await getJSON("/api/workspace");
    const health = await getJSON("/health");
    if (health.status !== "ok") throw new Error("el runtime local no confirmó su estado");
    data = payload;
    render();
    main.dataset.evidenceState = "current";
    $("#runtime").textContent = "Conectado · sólo lectura";
    $("#runtime-dot").classList.add("online");
    status.textContent = "Evidencia actualizada; ninguna señal fue aceptada.";
  } catch (failure) {
    clearWorkspace();
    main.dataset.evidenceState = "stale";
    $("#error-message").textContent = `Detalle: ${failure.message}. Comprueba el runtime local y vuelve a intentar.`;
    error.hidden = false;
    $("#runtime").textContent = "No disponible · lectura descartada";
    $("#runtime-dot").classList.remove("online");
    status.textContent = "No se actualizó la evidencia. No se realizó contacto, delivery ni escritura en CRM.";
  } finally {
    main.setAttribute("aria-busy", "false");
    refresh.disabled = false;
    retry.disabled = false;
    loading.hidden = true;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $$('[data-view]').forEach((button) => button.addEventListener("click", () => setView(button.dataset.view, { focus: true })));
  $("#refresh").addEventListener("click", load);
  $("#retry").addEventListener("click", load);
  load();
});
