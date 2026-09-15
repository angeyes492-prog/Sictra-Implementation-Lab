"use strict";
/* Presentation-only projection; never upgrades evidence or execution state. */
function validateOperations(data) {
  const text = x => typeof x === 'string' && x.length > 0;
  const timestamp = x => x === null || (Number.isFinite(x) && x >= 0);
  if (!data || data.scope !== 'LABORATORY_INTERNAL_SUPERVISED' || data.publication !== 'BLOCKED'
      || !['RUNNING','PAUSED','STOPPED','ERROR'].includes(data.status)
      || !text(data.control_token) || !timestamp(data.last_cycle)
      || typeof data.watch_enabled !== 'boolean' || !text(data.watch_directory)
      || !['profiles','outputs','waiting','intake_waiting'].every(k => Array.isArray(data[k]))
      || !data.profiles.every(p => p && text(p.id) && text(p.label))
      || !data.outputs.every(o => o && text(o.id) && text(o.title) && text(o.profile)
        && ['CURRENT','STALE_OR_REVOKED'].includes(o.availability))
      || new Set(data.outputs.map(o=>o.id)).size !== data.outputs.length
      || !data.waiting.every(w=>w && text(w.reason))
      || !data.intake_waiting.every(w=>w && text(w.job_id) && text(w.state))) {
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
    waiting:data.intake_waiting.length, alerts:data.intake_waiting.length+data.waiting.length,
    watch:data.watch_enabled ? 'Activa' : 'Inactiva',
    service:({RUNNING:'Servicio activo',PAUSED:'Servicio pausado',STOPPED:'Servicio detenido',ERROR:'Error · requiere recuperación'})[data.status]};
}
if (typeof module !== 'undefined') module.exports={validateOperations,operationProjection};
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
