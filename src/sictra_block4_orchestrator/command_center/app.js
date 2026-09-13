"use strict";
const escapeHTML = value => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const states = {
  BLOCK1_ATTESTED: ["Evidencia registrada", "active", "Consulta la procedencia antes de continuar la ruta."],
  BLOCK2_CANDIDATE: ["Candidato de diseño", "active", "Recibo de coordinación; no demuestra ejecución del Bloque 2."],
  BLOCK3_GOVERNED: ["Coordinación de precisión", "active", "Recibo de coordinación; no demuestra ejecución del Bloque 3."],
  HUMAN_REVIEW_REQUIRED: ["Revisión humana", "review", "El recorrido se detuvo para revisión humana. Consulta el historial y registra la decisión fuera de esta consola."],
  RETURN_UPSTREAM: ["Devuelto al origen", "blocked", "Revisa la evidencia de origen y la causa del retorno. Un reintento no resuelve una contradicción."],
  REJECTED: ["Rechazado", "blocked", "Consulta el historial antes de presentar una entrada corregida."],
  ABSTAINED: ["Abstención", "blocked", "El caso conserva una abstención; no debe interpretarse como aprobación."],
};
const stateInfo = state => Object.hasOwn(states, state) ? states[state] : ["Estado no reconocido", "blocked", "No se puede interpretar el estado recibido. Revisa el servicio local."];
function filteredCases(cases, query, filter) {
  const needle = query.trim().toLocaleLowerCase("es");
  return cases.filter(item => (!needle || `${item.case_id} ${item.run_id}`.toLocaleLowerCase("es").includes(needle)) && (filter === "all" || stateInfo(item.state)[1] === filter));
}
function validCases(payload) {
  if (!payload || !Array.isArray(payload.cases) || payload.authority?.acceptance !== "NOT_ACCEPTED") throw new Error("INVALID_RESPONSE");
  const ids = new Set();
  for (const item of payload.cases) {
    if (!item || ["case_id","run_id","state","certainty","disposition","expires_at","source_hash","provenance_root"].some(key => typeof item[key] !== "string") || !Number.isFinite(Date.parse(item.expires_at)) || ![item.lineage,item.restrictions].every(list => Array.isArray(list) && list.every(value => typeof value === "string")) || ids.has(item.case_id)) throw new Error("INVALID_CASE");
    ids.add(item.case_id);
  }
  return payload.cases;
}
const eventsLabel = {INGESTED:"Entró la evidencia",BLOCK2_COORDINATION_RECEIPT:"Coordinación · Design",BLOCK3_COORDINATION_RECEIPT:"Coordinación · Precision",HUMAN_GATE_REACHED:"Espera revisión humana",EXPIRED:"Evidencia vencida",INVALIDATED:"Evidencia invalidada",RETRY:"Reintento registrado"};
if (typeof module !== "undefined") module.exports = {escapeHTML, stateInfo, filteredCases, validCases};
if (typeof document !== "undefined") {
  const $ = selector => document.querySelector(selector);
  let cases = [], selected = null, auditVersion = 0, auditController = null;
  const date = value => new Date(value).toLocaleString("es", {dateStyle:"short",timeStyle:"short"});
  const chip = state => `<span class="state ${stateInfo(state)[1]}">${escapeHTML(stateInfo(state)[0])}</span>`;
  const pair = (label, value) => `<div><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value)}</dd></div>`;
  function detail(item) {
    if (!item) { $("#case-detail").innerHTML = '<p>No hay un caso seleccionado. Ajusta la búsqueda o incorpora un paquete mediante el operador local.</p>'; return; }
    const expired = Date.parse(item.expires_at) <= Date.now();
    const uncertainty = Array.isArray(item.uncertainty) ? item.uncertainty : [];
    const synthetic = uncertainty.includes("SYNTHETIC_FIELD_TEST_NOT_EVIDENCE");
    $("#case-detail").innerHTML = `<h3>${escapeHTML(item.case_id)}</h3>${chip(item.state)}<p>${escapeHTML(stateInfo(item.state)[2])}</p><p class="validity ${expired ? "expired" : ""}">${expired ? "Evidencia vencida. El estado registrado es histórico y requiere nueva revisión." : "Dentro del plazo declarado. La vigencia no demuestra la veracidad de la fuente."}</p>${synthetic ? '<p class="state review">Datos sintéticos de prueba · no constituyen evidencia real</p>' : ''}<dl>${pair("Estado",item.state)}${pair("Ejecución",item.run_id)}${pair("Certeza",item.certainty)}${pair("Disposición",item.disposition)}${pair("Ruta",item.lineage.join(" → "))}${pair("Vence",date(item.expires_at))}</dl><details><summary>Procedencia, incertidumbre y límites</summary><dl>${pair("Evidencia",item.evidence_id || "No disponible")}${pair("Dossier",item.dossier_id || "No disponible")}${pair("Incertidumbre",uncertainty.join(" · ") || "Sin declaración disponible")}${pair("Procedencia",item.provenance_root)}${pair("Hash fuente",item.source_hash)}${pair("Reintentos",item.retry_count)}${pair("Restricciones",item.restrictions.join(" · "))}</dl></details>`;
  }
  function clearAudit() {
    auditVersion++; auditController?.abort(); auditController = null;
    $("#audit-events").replaceChildren(); $("#audit-status").textContent = "Sin selección";
  }
  async function audit(id) {
    clearAudit(); if (!id) return;
    const version = auditVersion;
    const controller = new AbortController(); auditController = controller;
    const timer = setTimeout(() => controller.abort(), 10000);
    $("#audit-status").textContent = "Consultando historial…";
    try {
      const response = await fetch(`/api/cases/${encodeURIComponent(id)}/events`, {credentials:"same-origin",signal:controller.signal});
      if (!response.ok) throw new Error("AUDIT_UNAVAILABLE");
      const payload = await response.json();
      if (payload.case_id !== id || !Array.isArray(payload.events)) throw new Error("AUDIT_INVALID");
      if (version !== auditVersion) return;
      $("#audit-events").innerHTML = payload.events.map(event => `<li><strong>${escapeHTML(Object.hasOwn(eventsLabel,event.event_type) ? eventsLabel[event.event_type] : event.event_type)}</strong><time>${escapeHTML(date(event.created_at))}</time><small>${escapeHTML(event.state)}</small><details><summary>Ver registro</summary><pre>${escapeHTML(JSON.stringify(event.payload,null,2))}</pre></details></li>`).join("");
      $("#audit-status").textContent = payload.events.length ? `${payload.events.length} eventos · ${id}` : "Sin eventos registrados";
    } catch (_error) {
      if (version === auditVersion) { $("#audit-events").replaceChildren(); $("#audit-status").textContent = "Historial no disponible. Actualiza para reintentar."; }
    } finally { clearTimeout(timer); }
  }
  function render() {
    const visible = filteredCases(cases, $("#search").value, $("#state-filter").value);
    if (!visible.some(item => item.case_id === selected)) selected = visible[0]?.case_id || null;
    $("#result-count").textContent = `${visible.length} de ${cases.length}`;
    $("#case-list").innerHTML = visible.length ? visible.map(item => `<button class="case ${item.case_id===selected?"active":""}" type="button" aria-pressed="${item.case_id===selected}" data-case-id="${escapeHTML(item.case_id)}"><span><strong>${escapeHTML(item.case_id)}</strong><small>${escapeHTML(item.run_id)}</small><small>${escapeHTML(item.lineage.join(" → "))}</small></span>${chip(item.state)}</button>`).join("") : '<div class="empty-state">No hay casos para esta vista. Prueba otro filtro o incorpora un paquete local controlado.</div>';
    detail(cases.find(item => item.case_id === selected));
  }
  async function load() {
    clearAudit(); cases = []; selected = null;
    $("#main").setAttribute("aria-busy","true");
    for (const id of ["#refresh","#retry","#search","#state-filter"]) $(id).disabled = true;
    for (const id of ["#case-count","#review-count","#blocked-count","#last-read"]) $(id).textContent = "—";
    $("#error").hidden = true; $("#runtime-state").textContent = "Verificando lectura…";
    $("#refresh-status").textContent = "Actualizando casos…"; render();
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/api/cases",{credentials:"same-origin",signal:controller.signal});
      if (!response.ok) throw new Error("CASES_UNAVAILABLE");
      cases = validCases(await response.json());
      $("#case-count").textContent = String(cases.length);
      $("#review-count").textContent = String(cases.filter(item=>stateInfo(item.state)[1]==="review").length);
      $("#blocked-count").textContent = String(cases.filter(item=>stateInfo(item.state)[1]==="blocked").length);
      $("#last-read").textContent = new Date().toLocaleTimeString("es",{hour:"2-digit",minute:"2-digit"});
      $("#runtime-state").textContent = "Lectura verificada";
      $("#refresh-status").textContent = `${cases.length} casos actualizados. Ninguna decisión fue aprobada.`;
      render(); audit(selected);
    } catch (_error) {
      cases=[]; selected=null; render(); clearAudit(); $("#error").hidden=false;
      $("#runtime-state").textContent="Lectura detenida"; $("#refresh-status").textContent="Lectura fallida; resultados anteriores descartados.";
    } finally {
      clearTimeout(timer); $("#main").setAttribute("aria-busy","false");
      for (const id of ["#refresh","#retry","#search","#state-filter"]) $(id).disabled=false;
    }
  }
  $("#case-list").addEventListener("click", event => {
    const button=event.target.closest("[data-case-id]"); if(!button) return;
    selected=button.dataset.caseId; render();
    [...document.querySelectorAll("[data-case-id]")].find(item=>item.dataset.caseId===selected)?.focus(); audit(selected);
  });
  for(const id of ["#search","#state-filter"]) $(id).addEventListener("input",()=>{const previous=selected;render();if(previous!==selected)audit(selected);});
  $("#refresh").addEventListener("click",load); $("#retry").addEventListener("click",load);
  load();
}
