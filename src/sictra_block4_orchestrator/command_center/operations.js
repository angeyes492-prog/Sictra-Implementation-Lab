"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let token = "", loading = false, previewId = null;
  function closePreview() {
    previewId=null; $('operations-preview').hidden=true; $('draft-frame').src='about:blank';
    $('draft-text').removeAttribute('href');
  }
  const labels = {RUNNING:"Servicio activo",PAUSED:"Servicio pausado",STOPPED:"Servicio detenido",ERROR:"Servicio detenido por un error"};
  async function refresh() {
    if (loading) return;
    loading = true;
    const controller = new AbortController(), timer = setTimeout(()=>controller.abort(),10000);
    try {
      const response = await fetch('/api/operations', {signal:controller.signal});
      if (!response.ok) throw new Error('Servicio operativo no disponible. Inicia start_telecare.cmd.');
      const data = await response.json();
      token = data.control_token;
      if (previewId && !data.outputs.some(item=>item.id===previewId && item.availability==='CURRENT')) closePreview();
      $('operations-status').textContent = (labels[data.status] || 'Estado desconocido') + (data.data_class === 'SYNTHETIC_PILOT' ? ' · PRUEBA CON DATOS SINTÉTICOS' : '') + (data.last_cycle ? ' · Último ciclo: ' + new Date(data.last_cycle*1000).toLocaleTimeString('es') : '');
      $('operations-profiles').textContent = 'Perfiles: ' + data.profiles.map(p=>p.label).join(' · ');
      $('operations-watch').textContent = (data.watch_enabled ? 'Vigilancia activa: ' : 'Carpeta disponible para vigilancia: ') + data.watch_directory;
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
        description.textContent = item.profile + ' · ' + (item.availability === 'CURRENT' ? 'Borrador de investigación pendiente de revisión' : 'Fuente o perfil vencido: requiere actualización');
        content.append(title, description); article.append(content);
        if (item.availability === 'CURRENT') {
          const button = document.createElement('button'); button.type='button'; button.textContent='Leer borrador';
          button.addEventListener('click',()=>{ previewId=item.id; $('operations-preview').hidden=false; $('draft-frame').src='/api/operations/outputs/'+encodeURIComponent(item.id)+'/html'; $('draft-text').href='/api/operations/outputs/'+encodeURIComponent(item.id)+'/text'; });
          article.append(button);
        }
        $('operations-outputs').append(article);
      }
      if (!data.outputs.length) $('operations-outputs').textContent='Todavía no hay borradores. Registra una versión base y después una versión distinta del archivo marítimo autorizado.';
      $('operations-wait').textContent = data.waiting.map(w=>w.reason).join(' · ');
      for (const button of document.querySelectorAll('[data-operation]')) button.disabled=false;
    } catch (error) {
      token=''; $('operations-status').textContent=error.message; $('operations-outputs').replaceChildren();
      closePreview();
      for (const button of document.querySelectorAll('[data-operation]')) button.disabled=true;
    } finally {clearTimeout(timer); loading=false;}
  }
  async function post(path, value) {
    if (!token) throw new Error('Servicio no disponible.');
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),15000);
    try {
      const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Telecare-Control':token},body:JSON.stringify(value),signal:controller.signal});
      const data=await response.json(); if(!response.ok)throw new Error(data.error || 'Solicitud rechazada.');
      $('operations-feedback').textContent=data.status==='QUEUED'?'Archivo registrado. El servicio lo procesará en el próximo ciclo.':'Cambio registrado.';
      await refresh();
    } finally {clearTimeout(timer);}
  }
  document.querySelectorAll('[data-operation]').forEach(button=>button.addEventListener('click',()=>post('/api/operations/control',{action:button.dataset.operation}).catch(error=>$('operations-feedback').textContent=error.message)));
  $('operations-intake').addEventListener('submit',async event=>{
    event.preventDefault(); const button=$('intake-submit'); button.disabled=true;
    try {
      const file=$('intake-file').files[0]; if(!file || file.size>8388608 || !file.name.toLowerCase().endsWith('.xlsx'))throw new Error('Selecciona un archivo XLSX autorizado de hasta 8 MB.');
      const bytes=new Uint8Array(await file.arrayBuffer());
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
      let binary=''; for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
      await post('/api/operations/intake',{content:btoa(binary),sha256:digest,geo_level:$('intake-geo').value});
      $('operations-intake').reset();
    } catch(error){$('operations-feedback').textContent=error.message;} finally{button.disabled=false;}
  });
  $('operations-profile').addEventListener('submit',async event=>{
    event.preventDefault();
    try {
      await post('/api/operations/profile',{id:'operator-audience',label:$('profile-label').value,role:$('profile-role').value,depth:$('profile-depth').value,tone:$('profile-tone').value,geo_codes:$('profile-geo').value.split(',').map(x=>x.trim().toUpperCase()).filter(Boolean),questions:[],expires_at:Math.floor(Date.now()/1000)+90*86400});
    }catch(error){$('operations-feedback').textContent=error.message;}
  });
  $('close-preview').addEventListener('click',closePreview);
  refresh(); setInterval(()=>{if(!document.hidden)refresh();},5000);
})();
