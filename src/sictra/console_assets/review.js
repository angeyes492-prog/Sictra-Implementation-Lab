"use strict";
(() => {
  const $=id=>document.getElementById(id), block=Number(document.body.dataset.telecareBlock);
  let sequence=0, selectedId=null;
  function show(item) {
    selectedId=item.id;
    const target=$('review-detail');target.replaceChildren();target.hidden=false;
    const title=document.createElement('h3');title.textContent=item.title;target.append(title);
    const scope=document.createElement('p');scope.textContent='Revisión humana · publicación bloqueada · '+item.profile;target.append(scope);
    const links=document.createElement('nav');links.setAttribute('aria-label','Seguir este mismo artefacto');
    for(const [port,label] of [[8765,'Dossier fuente'],[8766,'Diseño'],[8767,'Adaptación'],[8768,'Orchestrator']]) {
      const a=document.createElement('a');a.textContent=label;
      a.href='http://127.0.0.1:'+port+'/?artifact='+encodeURIComponent(item.id)+'&dossier='+encodeURIComponent(item.dossier_id)+(port===8768?'#operations-outputs':'');
      links.append(a);
    }
    target.append(links);
    for(const section of item.content.content_blocks) {
      const wrap=document.createElement('section'), heading=document.createElement('h4'), body=document.createElement('p');
      heading.textContent=section.title || section.kind;body.textContent=section.body;
      wrap.append(heading,body);target.append(wrap);
    }
    const details=document.createElement('details'), summary=document.createElement('summary'), code=document.createElement('pre');
    summary.textContent='Identidad, evidencia y contrato';code.textContent=JSON.stringify({case_id:item.case_id,dossier_id:item.dossier_id,evidence_id:item.evidence_id,source_hash:item.source_hash,artifact_fingerprint:item.artifact_fingerprint,content:item.content},null,2);
    details.append(summary,code);target.append(details);
  }
  async function load() {
    const request=++sequence, controller=new AbortController(), timer=setTimeout(()=>controller.abort(),10000);
    $('review-list').replaceChildren();$('review-detail').replaceChildren();$('review-detail').hidden=true;
    $('review-status').textContent='Verificando vigencia e integridad…';
    try {
      const response=await fetch('/api/review-artifacts',{signal:controller.signal});
      if(!response.ok)throw new Error('No se pudo verificar la cadena. No se conservan artefactos anteriores.');
      const data=await response.json();
      if(data.block!==block || data.publication!=='BLOCKED' || data.acceptance!=='NOT_ACCEPTED' || !Array.isArray(data.artifacts)
        || !data.artifacts.every(x=>typeof x.id==='string' && x.publication==='BLOCKED' && Array.isArray(x.content?.content_blocks)))throw new Error('Respuesta fuera del contrato de revisión.');
      if(request!==sequence)return;
      $('review-status').textContent=data.status==='NOT_CONFIGURED'?'Cadena no conectada. Inicia los cuatro bloques con start_telecare.cmd.':data.artifacts.length+' artefactos vigentes · '+data.unavailable.length+' no disponibles por vigencia o integridad.';
      const requested=selectedId || new URLSearchParams(location.search).get('artifact');
      for(const item of data.artifacts) {
        const button=document.createElement('button');button.type='button';button.textContent=item.title+' · '+item.profile;
        button.addEventListener('click',()=>show(item));$('review-list').append(button);
      }
      if(requested) {
        const match=data.artifacts.find(item=>item.id===requested);
        if(match)show(match);else $('review-status').textContent='El artefacto solicitado no está vigente en esta cadena. No se sustituyó por otro.';
      }
    } catch(error) {
      if(request===sequence){$('review-list').replaceChildren();$('review-detail').replaceChildren();$('review-detail').hidden=true;$('review-status').textContent=error.message;}
    } finally {clearTimeout(timer);}
  }
  $('review-refresh').addEventListener('click',load);load();
  // Revalidate on return to the console; never imply a previous read is current.
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)load();});
  setInterval(()=>{if(!document.hidden)load();},15000);
})();
