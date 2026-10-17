"use strict";
/* Presentation-only projection; never upgrades evidence or execution state. */
function validateOperations(data) {
  const text = x => typeof x === 'string' && x.length > 0;
  const timestamp = x => x === null || (Number.isFinite(x) && x >= 0);
  const routes={INDEPENDENT_CORROBORATION:'INDEPENDENT_DOSSIER',SOURCE_METHODOLOGY:'OFFICIAL_SOURCE_METHODOLOGY',
    COMPANY_EXPOSURE:'AUTHORIZED_ACCOUNT_CONTEXT',SOURCE_GRANULARITY:'SOURCE_SCOPE_DETAIL',UNCLASSIFIED:'MANUAL_CLASSIFICATION'};
  const contextValid = d => d.change_context === undefined || d.change_context === null ||
    d.status === 'CURRENT' && d.change_context.dossier_id === d.dossier_id &&
    d.change_context.scope === 'LOCAL_LITERAL_CHANGE_CONTEXT' && d.change_context.version === '0.1.0' &&
    d.change_context.source_hash === d.source_hash && /^[0-9a-f]{64}$/.test(d.change_context.source_hash) &&
    /^[0-9a-f]{64}$/.test(d.change_context.dossier_sha256) &&
    d.change_context.cause_certainty === 'UNCONFIRMED' && d.change_context.resolution === 'NOT_RESOLVED' &&
    d.change_context.acceptance === 'NOT_ACCEPTED' && d.change_context.publication === 'BLOCKED' &&
    Array.isArray(d.change_context.facts) && d.change_context.facts.length > 0 &&
    d.change_context.facts.every(f => f && text(f.fact_id) && text(f.geography) && text(f.before_period) && text(f.after_period) &&
      (['SAME_PERIOD_REPORTED_VALUE_CHANGE','SAME_PERIOD_STATUS_FLAG_CHANGE','OBSERVATION_COVERAGE_ADDED',
        'OBSERVATION_COVERAGE_REMOVED'].includes(f.kind) && f.unit === 'THOUSAND_TONNES' && f.before_period === f.after_period ||
       f.kind === 'DISTINCT_PERIOD_VALUE_COMPARISON' && f.unit === 'USD_MILLION' && f.before_period < f.after_period));
  if (!data || data.scope !== 'LABORATORY_INTERNAL_SUPERVISED' || data.publication !== 'BLOCKED'
      || !['RUNNING','PAUSED','STOPPED','ERROR'].includes(data.status)
      || !text(data.control_token) || !timestamp(data.last_cycle)
      || typeof data.watch_enabled !== 'boolean' || !text(data.watch_directory)
      || !['profiles','outputs','waiting','intake_waiting','autonomy_tasks','dossier_evidence'].every(k => Array.isArray(data[k]))
      || !data.dossier_evidence.every(d=>d && text(d.dossier_id)
        && ['CURRENT','UNAVAILABLE'].includes(d.status) && Number.isFinite(d.checked_at) && contextValid(d))
      || !data.profiles.every(p => p && text(p.id) && text(p.label))
      || !data.outputs.every(o => o && text(o.id) && text(o.title) && text(o.profile)
        && ['CURRENT','STALE_OR_REVOKED'].includes(o.availability))
      || new Set(data.outputs.map(o=>o.id)).size !== data.outputs.length
      || !data.waiting.every(w=>w && text(w.reason))
      || !data.intake_waiting.every(w=>w && text(w.job_id) && text(w.state))
      || !data.autonomy_tasks.every(t=>t && text(t.task_id) && text(t.dossier_id)
        && ['CURRENT','UNAVAILABLE'].includes(t.source_evidence_status)
        && text(t.state) && text(t.requirement) && text(t.required_evidence_root)
        && ['INDEPENDENT_CORROBORATION','SOURCE_METHODOLOGY','COMPANY_EXPOSURE',
            'SOURCE_GRANULARITY','UNCLASSIFIED'].includes(t.effective_kind)
        && (t.effective_evidence_route===undefined || t.effective_evidence_route===routes[t.effective_kind])
        && t.effective_completion_boundary==='BLOCK1_CONTRACTED_RESOLUTION_REQUIRED'
        && ['CURRENT','LEGACY_SUPERSEDED'].includes(t.boundary_status)
        && ['NOT_LINKED','CURRENT','STALE_OR_REVOKED'].includes(t.evidence_status)
        && (t.research_evaluation===null || t.research_evaluation &&
          t.research_evaluation.task_id===t.task_id && text(t.research_evaluation.id) &&
          (t.research_evaluation.availability==='STALE_OR_REVOKED' && !('verdict' in t.research_evaluation)
           || t.research_evaluation.availability==='CURRENT_INPUTS'
           && ['WAITING_LOCAL_EVIDENCE','WAITING_TASK_SPECIFIC_EVIDENCE','INSUFFICIENT','MEASUREMENT_DISAGREEMENT','REVIEW_REQUIRED'].includes(t.research_evaluation.verdict)
           && (t.research_evaluation.verdict!=='WAITING_TASK_SPECIFIC_EVIDENCE'
               || ['OFFICIAL_SOURCE_METHODOLOGY','AUTHORIZED_ACCOUNT_CONTEXT','SOURCE_SCOPE_DETAIL','MANUAL_CLASSIFICATION'].includes(t.effective_evidence_route)
               && t.research_evaluation.candidate===null)
           && t.research_evaluation.scope==='ADMITTED_LOCAL_DOSSIERS_ONLY'
           && t.research_evaluation.resolution==='NOT_RESOLVED'
           && t.research_evaluation.acceptance==='NOT_ACCEPTED'
           && t.research_evaluation.publication==='BLOCKED'))
        && (t.evidence_comparison===null || t.evidence_comparison &&
          ['NO_SHARED_MEASUREMENT','PARTIAL_COVERAGE_REVIEW_REQUIRED',
           'VALUE_DIFFERENCE_REVIEW_REQUIRED','EXACT_VALUE_AGREEMENT_REVIEW_REQUIRED'].includes(t.evidence_comparison.status)
          && t.evidence_comparison.primary_dossier_id===t.dossier_id
          && text(t.evidence_comparison.candidate_dossier_id)
          && Array.isArray(t.evidence_comparison.matched)
          && t.evidence_comparison.resolution==='NOT_RESOLVED'
          && t.evidence_comparison.publication==='BLOCKED')
        && (t.evidence_assessment===null || t.evidence_assessment &&
          ['INSUFFICIENT','MEASUREMENT_DISAGREEMENT','REVIEW_REQUIRED'].includes(t.evidence_assessment.verdict)
          && text(t.evidence_assessment.reason_code) && text(t.evidence_assessment.next_action)
          && t.evidence_assessment.need_kind===t.effective_kind
          && t.evidence_assessment.primary_dossier_id===t.dossier_id
          && t.evidence_assessment.candidate_dossier_id===t.evidence_comparison.candidate_dossier_id
          && t.evidence_assessment.comparison_status===t.evidence_comparison.status
          && t.evidence_assessment.resolution==='NOT_RESOLVED'
          && t.evidence_assessment.acceptance==='NOT_ACCEPTED'
          && t.evidence_assessment.publication==='BLOCKED')
        && (t.evidence_assessment===null)===(t.evidence_comparison===null))) {
    throw new Error('Lectura operativa incompleta o fuera del alcance autorizado.');
  }
  const run = data.orchestration?.last_run;
  if (run && (!Number.isFinite(run.requested_at) || !text(run.cycle?.state))) {
    throw new Error('Identidad del último ciclo no disponible.');
  }
  return data;
}
function operationProjection(data) {
  validateOperations(data);
  return {current:data.outputs.filter(o=>o.availability==='CURRENT').length,
    stale:data.outputs.filter(o=>o.availability!=='CURRENT').length,
    waiting:data.intake_waiting.length, alerts:data.intake_waiting.length+data.waiting.length+data.autonomy_tasks.length,
    watch:data.watch_enabled ? 'Activa' : 'Inactiva',
    service:({RUNNING:'Servicio activo',PAUSED:'Servicio pausado',STOPPED:'Servicio detenido',ERROR:'Error · requiere recuperación'})[data.status]};
}
function changeContextLabel(context) {
  if (!context) return '';
  const labels={SAME_PERIOD_REPORTED_VALUE_CHANGE:'Valor reportado cambiado en el mismo periodo',
    SAME_PERIOD_STATUS_FLAG_CHANGE:'Bandera de estado cambiada en el mismo periodo',
    OBSERVATION_COVERAGE_ADDED:'Observación añadida',OBSERVATION_COVERAGE_REMOVED:'Observación retirada',
    DISTINCT_PERIOD_VALUE_COMPARISON:'Comparación entre periodos distintos'};
  return [...new Set(context.facts.map(f=>labels[f.kind]))].join(' / ')+' · causa no confirmada';
}
if (typeof module !== 'undefined') module.exports={validateOperations,operationProjection,changeContextLabel};
if (typeof document !== 'undefined') {
  document.addEventListener('telecare:operations', event => {
    const data=event.detail, put=(id,value)=>document.getElementById(id).textContent=value;
    if (!data) {
      for(const id of ['scene-output-count','scene-current','scene-stale','scene-wait-count','scene-alert-count','scene-watch']) put(id,'—');
      put('scene-service','Servicio no disponible'); put('scene-output-note','Lectura fallida; resultados descartados.');
      put('scene-alert-text','No se pudo verificar la operación'); put('scene-run','Sin lectura verificada');
      put('scene-class','El escenario es una ilustración, no un mapa de operaciones.');
      return;
    }
    const view=operationProjection(data);
    put('scene-service',view.service);put('scene-watch',view.watch);
    put('scene-output-count',data.outputs.length);put('scene-current',view.current);put('scene-stale',view.stale);
    put('scene-wait-count',view.waiting);put('scene-alert-count',view.alerts);
    put('scene-alert-text',view.alerts ? 'Consulta causas y recuperación' : 'Sin esperas registradas en esta lectura');
    put('scene-output-note',data.outputs.length ? 'Borradores locales · no publicados' : 'Registra una base y una versión distinta para preparar un boletín.');
    const run=data.orchestration?.last_run;
    put('scene-run',run ? 'Última orden · '+new Date(run.requested_at*1000).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'})+' · '+run.cycle.state : 'Todavía no hay una orden integral registrada.');
    put('scene-class',data.data_class==='SYNTHETIC_PILOT' ? 'DATOS SINTÉTICOS · prueba local, no evidencia real.' : 'Escenario ilustrativo. Indicadores del servicio local.');
  });
  // Anchor destinations may live inside a closed disclosure. Reveal before focus.
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href^="#"]');
    if(!link || link.hash.length<2) return;
    const target=document.getElementById(link.hash.slice(1));
    if(!target)return;
    let parent=target.closest('details');
    while(parent){parent.open=true;parent=parent.parentElement.closest('details');}
    target.setAttribute('tabindex','-1');target.focus({preventScroll:true});
  });
}
