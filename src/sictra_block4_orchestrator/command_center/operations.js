"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let token = "", loading = false, previewId = null, posting = false, lastStatus = null;
  let requestedArtifact=new URLSearchParams(location.search).get('artifact');
  function openPreview(id, factsheet=false) {
    previewId=id; $('operations-preview').hidden=false;
    $('draft-frame').src='/api/operations/outputs/'+encodeURIComponent(id)+(factsheet?'/factsheet':'/html');
    $('preview-title').textContent=factsheet?'Ficha de trazabilidad':'Boletín de revisión diseñado';
    $('draft-factsheet').href='/api/operations/outputs/'+encodeURIComponent(id)+'/factsheet.json';
    $('draft-text').href='/api/operations/outputs/'+encodeURIComponent(id)+'/text';
  }
  function controls() {
    for (const button of document.querySelectorAll('[data-operation]')) {
      const action=button.dataset.operation;
      button.disabled=!token || posting || (['execute','resume'].includes(action) && ['STOPPED','ERROR'].includes(lastStatus))
        || (action==='execute' && lastStatus!=='RUNNING')
        || (action==='pause' && lastStatus!=='RUNNING') || (action==='resume' && lastStatus!=='PAUSED');
    }
  }
  function closePreview() {
    previewId=null; $('operations-preview').hidden=true; $('draft-frame').src='about:blank';
    $('draft-text').removeAttribute('href');
    $('draft-factsheet').removeAttribute('href');
  }
  const labels = {RUNNING:"Servicio activo",PAUSED:"Servicio pausado",STOPPED:"Servicio detenido",ERROR:"Servicio detenido por un error"};
  function profileId(label) {
    const normalized=label.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,48);
    return 'audience-'+(normalized || 'segment');
  }
  async function refresh() {
    if (loading) return;
    loading = true;
    const controller = new AbortController(), timer = setTimeout(()=>controller.abort(),10000);
    try {
      const response = await fetch('/api/operations', {signal:controller.signal});
      if (!response.ok) throw new Error('Servicio operativo no disponible. Inicia start_telecare.cmd.');
      const data = validateOperations(await response.json());
      token = data.control_token;
      lastStatus=data.status;
      $('review-policy-status').textContent=data.evidence_review_deferred ? 'Revisión de evidencia diferida · la construcción y los ciclos locales continúan.' : 'Cada cambio espera revisión de evidencia.';
      $('deferred-reviews').replaceChildren();
      for(const item of data.deferred_reviews || []) {const row=document.createElement('li');row.textContent=item.dossier_id+' · Cerrado por abstención · evidencia pendiente · no aceptado';$('deferred-reviews').append(row);}
      $('autonomy-task-list').replaceChildren();
      for (const item of data.autonomy_tasks) {
        const card=document.createElement('article');card.className='case';
        const text=document.createElement('div'), title=document.createElement('strong'), body=document.createElement('p');
        title.textContent=item.kind+' · '+item.state;
        body.textContent=item.requirement+' · raíz requerida: '+item.required_evidence_root;
        text.append(title,body);card.append(text);
        if (item.state==='OPEN') {
          const button=document.createElement('button');button.type='button';button.textContent='Registrar lectura humana';
          button.addEventListener('click',()=>{
            const reviewer=prompt('Identificador del revisor local:');
            const rationale=prompt('Explica qué evidencia falta y la siguiente acción (20–1000 caracteres):');
            if(reviewer&&rationale) post('/api/operations/tasks/review',{task_id:item.task_id,reviewer_id:reviewer,rationale}).catch(error=>$('operations-feedback').textContent=error.message);
          });card.append(button);
        }
        $('autonomy-task-list').append(card);
      }
      if (!data.autonomy_tasks.length) $('autonomy-task-list').textContent='No hay tareas derivadas de un dossier vigente.';
      document.dispatchEvent(new CustomEvent('telecare:operations',{detail:data}));
      if (previewId && !data.outputs.some(item=>item.id===previewId && item.availability==='CURRENT')) closePreview();
      $('operations-status').textContent = (labels[data.status] || 'Estado desconocido') + (data.data_class === 'SYNTHETIC_PILOT' ? ' · PRUEBA CON DATOS SINTÉTICOS' : '') + (data.last_cycle ? ' · Último ciclo: ' + new Date(data.last_cycle*1000).toLocaleTimeString('es') : '');
      $('operations-profiles').textContent = 'Perfiles: ' + data.profiles.map(p=>p.label).join(' · ');
      $('operations-watch').textContent = (data.watch_enabled ? 'Vigilancia activa: ' : 'Carpeta disponible para vigilancia: ') + data.watch_directory;
      const run=data.orchestration && data.orchestration.last_run;
      $('operations-orchestration').textContent = run ? 'Última orden integral: ' + new Date(run.requested_at*1000).toLocaleTimeString('es') + ' · ' + run.cycle.state + ' · publicación bloqueada.' : 'Sin orden integral registrada. Configura una fuente local aprobada y ejecuta el ciclo.';
      $('operations-recovery').replaceChildren();
      for (const job of data.intake_waiting) {
        const row=document.createElement('p'), button=document.createElement('button');
        row.textContent='Entrada pendiente de revisión: '+job.job_id.slice(0,12)+' · '+job.state+' ';
        button.type='button';button.textContent='Registrar abstención y permitir la siguiente entrada';
        button.addEventListener('click',()=>post('/api/operations/abstain',{job_id:job.job_id,reason:'El operador conserva el dossier para revisión y se abstiene de aceptar esta entrada.'}).catch(error=>$('operations-feedback').textContent=error.message));
        row.append(button);$('operations-recovery').append(row);
      }
      $('operations-outputs').replaceChildren();
      for (const item of data.outputs) {
        const article = document.createElement('article'); article.className='case';
        const content = document.createElement('div'), title = document.createElement('strong'), description = document.createElement('p');
        title.textContent = item.title;
        description.textContent = item.profile + ' · ' + (item.availability === 'CURRENT' ? 'Boletín diseñado pendiente de revisión' : 'Fuente o perfil vencido: requiere actualización');
        content.append(title, description); article.append(content);
        if (item.availability === 'CURRENT') {
          const button = document.createElement('button'); button.type='button'; button.textContent='Abrir boletín';
          button.addEventListener('click',()=>openPreview(item.id));
          article.append(button);
          const sheetButton=document.createElement('button');sheetButton.type='button';sheetButton.textContent='Ficha de trazabilidad';
          sheetButton.addEventListener('click',()=>openPreview(item.id,true));article.append(sheetButton);
          const links=document.createElement('div');links.className='artifact-links';
          for(const [port,label] of [[8765,'Dossier'],[8766,'Diseño'],[8767,'Adaptación']]) {
            const link=document.createElement('a');link.textContent=label;
            link.href='http://127.0.0.1:'+port+'/?artifact='+encodeURIComponent(item.id)+'&dossier='+encodeURIComponent(item.dossier_id || '');links.append(link);
          }
          article.append(links);
        }
        $('operations-outputs').append(article);
      }
      if (!data.outputs.length) $('operations-outputs').textContent='Todavía no hay boletines. Registra una versión base y después una versión distinta de la fuente marítima autorizada.';
      if(requestedArtifact){const match=data.outputs.find(item=>item.id===requestedArtifact&&item.availability==='CURRENT');if(match)openPreview(match.id);else $('operations-feedback').textContent='El boletín solicitado no está vigente o no pertenece a esta cadena. No se sustituyó por otro.';requestedArtifact=null;}
      $('operations-wait').textContent = data.waiting.map(w=>w.reason).join(' · ');
      controls();
    } catch (error) {
      token=''; $('operations-status').textContent=error.message; $('operations-outputs').replaceChildren();
      closePreview();
      document.dispatchEvent(new CustomEvent('telecare:operations',{detail:null}));
      for(const id of ['operations-profiles','operations-watch','operations-orchestration','operations-wait','review-policy-status']) $(id).textContent='';
      $('deferred-reviews').replaceChildren();
      $('autonomy-task-list').replaceChildren();
      $('operations-recovery').replaceChildren();
      for (const button of document.querySelectorAll('[data-operation]')) button.disabled=true;
    } finally {clearTimeout(timer); loading=false;}
  }
  async function post(path, value) {
    if (!token) throw new Error('Servicio no disponible.');
    if (posting) return;
    posting=true;controls();
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),15000);
    try {
      const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Telecare-Control':token},body:JSON.stringify(value),signal:controller.signal});
      const data=await response.json(); if(!response.ok)throw new Error(data.error || 'Solicitud rechazada.');
      $('operations-feedback').textContent=data.status==='QUEUED'?'Archivo registrado. El servicio lo procesará en el próximo ciclo.':data.status==='ORCHESTRATION_EXECUTED'?'Ciclo integral ejecutado. La vigilancia de fuente aprobada quedó activa; las salidas siguen en revisión humana.':data.status==='PAUSED'?'El servicio está pausado. Reanúdalo antes de ejecutar.':data.status==='STOPPED'?'Servicio detenido. Se requiere reinicio explícito; no se ejecutó un ciclo.':'Cambio registrado.';
      await refresh();
    } finally {clearTimeout(timer);posting=false;controls();}
  }
  document.querySelectorAll('[data-operation]').forEach(button=>button.addEventListener('click',()=>post('/api/operations/control',{action:button.dataset.operation}).catch(error=>$('operations-feedback').textContent=error.message)));
  $('operations-intake').addEventListener('submit',async event=>{
    event.preventDefault(); const button=$('intake-submit'); button.disabled=true;
    try {
      const file=$('intake-file').files[0]; if(!file || file.size>8388608 || !file.name.toLowerCase().endsWith('.xlsx'))throw new Error('Selecciona un archivo XLSX autorizado de hasta 8 MB.');
      const bytes=new Uint8Array(await file.arrayBuffer());
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
      let binary=''; for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
      const sourceType=$('intake-source').value;
      await post('/api/operations/intake',{content:btoa(binary),sha256:digest,source_type:sourceType,geo_level:sourceType==='HN_CUSTOMS_Q1_V1'?'CUSTOMS_POINT':$('intake-geo').value});
      $('operations-intake').reset();
      $('intake-geo-label').hidden=false;
    } catch(error){$('operations-feedback').textContent=error.message;} finally{button.disabled=false;}
  });
  $('intake-source').addEventListener('change',()=>{
    const hn=$('intake-source').value==='HN_CUSTOMS_Q1_V1';
    $('intake-geo-label').hidden=hn;
  });
  $('operations-profile').addEventListener('submit',async event=>{
    event.preventDefault();
    try {
      const label=$('profile-label').value.trim();
      await post('/api/operations/profile',{id:profileId(label),label,role:$('profile-role').value,depth:$('profile-depth').value,tone:$('profile-tone').value,geo_codes:$('profile-geo').value.split(',').map(x=>x.trim().toUpperCase()).filter(Boolean),questions:[],expires_at:Math.floor(Date.now()/1000)+90*86400});
    }catch(error){$('operations-feedback').textContent=error.message;}
  });
  $('close-preview').addEventListener('click',closePreview);
  refresh(); setInterval(()=>{if(!document.hidden)refresh();},5000);
})();
