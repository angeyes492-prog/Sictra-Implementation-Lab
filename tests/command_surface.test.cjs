const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {validateOperations,operationProjection}=require('../src/sictra_block4_orchestrator/command_center/command.js');
const fixture=()=>({scope:'LABORATORY_INTERNAL_SUPERVISED',publication:'BLOCKED',status:'PAUSED',
 control_token:'local-test-token',last_cycle:1789300800,watch_enabled:false,watch_directory:'local/dropbox',
 profiles:[{id:'ops',label:'Operaciones'}],outputs:[{id:'one',title:'Dossier',profile:'Operaciones',availability:'CURRENT'},
 {id:'two',title:'Antiguo',profile:'Operaciones',availability:'STALE_OR_REVOKED'}],
 intake_waiting:[{job_id:'input-1',state:'REVIEW_REQUIRED'}],waiting:[{reason:'MISSING_PROFILE'}],
 autonomy_tasks:[{task_id:'TASK-1',dossier_id:'dossier-1',state:'OPEN',requirement:'Fuente independiente',required_evidence_root:'MUST_DIFFER_FROM:root-a'}],orchestration:{last_run:null}});
test('projects actual availability without calling stale outputs current or completed',()=>{
 const input=fixture(); assert.deepEqual(operationProjection(input),{current:1,stale:1,waiting:1,alerts:3,watch:'Inactiva',service:'Servicio pausado'});
 assert.equal(input.publication,'BLOCKED');assert.equal(input.outputs[1].availability,'STALE_OR_REVOKED');
});
test('empty is zero only after valid reading; missing state is not zero',()=>{
 const input=fixture();input.outputs=[];assert.equal(operationProjection(input).current,0);
 for(const key of ['outputs','profiles','waiting','intake_waiting','autonomy_tasks','control_token','watch_enabled','scope','publication']){
  const broken=fixture();delete broken[key];assert.throws(()=>validateOperations(broken));
 }
 assert.throws(()=>operationProjection(null));
});
test('unknown state, unsafe authority and duplicate identities fail closed',()=>{
 for(const patch of [{status:'GREEN'},{publication:'ALLOWED'},{scope:'PRODUCTION'},{last_cycle:'yesterday'}])assert.throws(()=>validateOperations({...fixture(),...patch}));
 const duplicate=fixture();duplicate.outputs.push({...duplicate.outputs[0]});assert.throws(()=>validateOperations(duplicate));
 const unknown=fixture();unknown.outputs[0].availability='ACCEPTED';assert.throws(()=>validateOperations(unknown));
 const malformed=fixture();malformed.orchestration.last_run={requested_at:1,cycle:{state:null}};assert.throws(()=>validateOperations(malformed));
});
test('untrusted labels remain strings, not markup instructions',()=>{
 const input=fixture();input.outputs[0].title='<img src=x onerror=alert(1)>';
 assert.equal(validateOperations(input).outputs[0].title,'<img src=x onerror=alert(1)>');
 assert.equal(operationProjection(input).current,1);
});
test('Intelligence does not infer numeric uncertainty from counts or fabricate source age',()=>{
 const source=fs.readFileSync(require.resolve('../src/sictra_block1/web/app.js'),'utf8');
 const sandbox={URLSearchParams,document:{addEventListener(){}}};vm.createContext(sandbox);vm.runInContext(source,sandbox);
 assert.equal(sandbox.overviewUncertainty({evidence_summary:{sources:99,independent_roots:99,contradictions:0}}),'No cuantificada');
 assert.equal(sandbox.overviewUncertainty({evidence_summary:{sources:0,independent_roots:0,contradictions:8}}),'No cuantificada');
 assert.ok(source.includes('Sin fecha verificada'));assert.ok(!source.includes('age=[4,7,11,1]'));
 assert.equal(sandbox.requestedDossier('?dossier=eurostat:abc',{status:'AVAILABLE',dossiers:[{dossier_id:'eurostat:abc'}]}),'eurostat:abc');
 assert.equal(sandbox.requestedDossier('?dossier=other',{status:'AVAILABLE',dossiers:[{dossier_id:'eurostat:abc'}]}),false);
 assert.equal(sandbox.requestedDossier('?dossier=eurostat:abc',{status:'INTEGRITY_ERROR',dossiers:[{dossier_id:'eurostat:abc'}]}),false);
 assert.equal(sandbox.requestedDossier('?dossier=%3Cscript%3E',{status:'AVAILABLE',dossiers:[]}),false);
});
