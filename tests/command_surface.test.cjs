const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {validateOperations,operationProjection,changeContextLabel}=require('../src/sictra_block4_orchestrator/command_center/command.js');
const fixture=()=>({scope:'LABORATORY_INTERNAL_SUPERVISED',publication:'BLOCKED',status:'PAUSED',
 control_token:'local-test-token',last_cycle:1789300800,watch_enabled:false,watch_directory:'local/dropbox',
 profiles:[{id:'ops',label:'Operaciones'}],outputs:[{id:'one',title:'Dossier',profile:'Operaciones',availability:'CURRENT'},
 {id:'two',title:'Antiguo',profile:'Operaciones',availability:'STALE_OR_REVOKED'}],
 intake_waiting:[{job_id:'input-1',state:'REVIEW_REQUIRED'}],waiting:[{reason:'MISSING_PROFILE'}],
 dossier_evidence:[{dossier_id:'dossier-1',status:'CURRENT',checked_at:1789300800}],
 autonomy_tasks:[{task_id:'TASK-1',dossier_id:'dossier-1',state:'OPEN',requirement:'Fuente independiente',required_evidence_root:'MUST_DIFFER_FROM:root-a',evidence_status:'NOT_LINKED',evidence_comparison:null,evidence_assessment:null,research_evaluation:null,source_evidence_status:'CURRENT',effective_kind:'UNCLASSIFIED',effective_completion_boundary:'BLOCK1_CONTRACTED_RESOLUTION_REQUIRED',boundary_status:'CURRENT'}],orchestration:{last_run:null}});
test('projects actual availability without calling stale outputs current or completed',()=>{
 const input=fixture(); assert.deepEqual(operationProjection(input),{current:1,stale:1,waiting:1,alerts:3,watch:'Inactiva',service:'Servicio pausado'});
 assert.equal(input.publication,'BLOCKED');assert.equal(input.outputs[1].availability,'STALE_OR_REVOKED');
});
test('empty is zero only after valid reading; missing state is not zero',()=>{
 const input=fixture();input.outputs=[];assert.equal(operationProjection(input).current,0);
 for(const key of ['outputs','profiles','waiting','intake_waiting','autonomy_tasks','dossier_evidence','control_token','watch_enabled','scope','publication']){
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
test('linked evidence and reassessment requests remain alerts, even before expiry',()=>{
 const input=fixture();input.autonomy_tasks[0].state='EVIDENCE_LINKED_REVIEW_REQUIRED';input.autonomy_tasks[0].evidence_status='CURRENT';
 assert.equal(operationProjection(input).alerts,3);
 input.autonomy_tasks[0].state='BLOCK1_REASSESSMENT_REQUIRED';assert.equal(operationProjection(input).alerts,3);
 input.autonomy_tasks[0].evidence_status='STALE_OR_REVOKED';assert.equal(operationProjection(input).alerts,3);
 input.autonomy_tasks[0].evidence_status='ACCEPTED';assert.throws(()=>validateOperations(input));
});
test('legacy task boundary is explicit and a forged resolved boundary is rejected',()=>{
 const input=fixture();input.autonomy_tasks[0].boundary_status='LEGACY_SUPERSEDED';
 assert.equal(validateOperations(input).autonomy_tasks[0].boundary_status,'LEGACY_SUPERSEDED');
 input.autonomy_tasks[0].effective_completion_boundary='HUMAN_REVIEW_IS_ENOUGH';
 assert.throws(()=>validateOperations(input));
});
test('expired task sources remain visible and unknown currentness fails closed',()=>{
 const input=fixture();input.dossier_evidence[0].status='UNAVAILABLE';input.autonomy_tasks[0].source_evidence_status='UNAVAILABLE';
 assert.equal(validateOperations(input).autonomy_tasks[0].state,'OPEN');
 assert.equal(operationProjection(input).alerts,3);
 input.autonomy_tasks[0].source_evidence_status='ACCEPTED';assert.throws(()=>validateOperations(input));
 input.autonomy_tasks[0].source_evidence_status='CURRENT';input.dossier_evidence[0].status='VERIFIED';
 assert.throws(()=>validateOperations(input));
});
test('comparison remains unresolved and false resolution is rejected',()=>{
 const input=fixture();input.autonomy_tasks[0].evidence_comparison={primary_dossier_id:'dossier-1',candidate_dossier_id:'dossier-2',matched:[],status:'NO_SHARED_MEASUREMENT',resolution:'NOT_RESOLVED',publication:'BLOCKED'};
 input.autonomy_tasks[0].evidence_assessment={need_kind:'UNCLASSIFIED',primary_dossier_id:'dossier-1',candidate_dossier_id:'dossier-2',comparison_status:'NO_SHARED_MEASUREMENT',verdict:'INSUFFICIENT',reason_code:'NO_SHARED_MEASUREMENT',next_action:'REQUEST_COMPARABLE_APPROVED_SOURCE',resolution:'NOT_RESOLVED',acceptance:'NOT_ACCEPTED',publication:'BLOCKED'};
 assert.equal(validateOperations(input).autonomy_tasks[0].evidence_comparison.status,'NO_SHARED_MEASUREMENT');
 input.autonomy_tasks[0].evidence_comparison.resolution='RESOLVED';assert.throws(()=>validateOperations(input));
});
test('assessment cannot promote task or disappear from an active comparison',()=>{
 const input=fixture();input.autonomy_tasks[0].evidence_comparison={primary_dossier_id:'dossier-1',candidate_dossier_id:'dossier-2',matched:[],status:'NO_SHARED_MEASUREMENT',resolution:'NOT_RESOLVED',publication:'BLOCKED'};
 assert.throws(()=>validateOperations(input));
 input.autonomy_tasks[0].evidence_assessment={need_kind:'UNCLASSIFIED',primary_dossier_id:'dossier-1',candidate_dossier_id:'dossier-2',comparison_status:'NO_SHARED_MEASUREMENT',verdict:'INSUFFICIENT',reason_code:'NO_SHARED_MEASUREMENT',next_action:'REQUEST_COMPARABLE_APPROVED_SOURCE',resolution:'NOT_RESOLVED',acceptance:'NOT_ACCEPTED',publication:'BLOCKED'};
 assert.equal(validateOperations(input).autonomy_tasks[0].evidence_assessment.verdict,'INSUFFICIENT');
 input.autonomy_tasks[0].evidence_assessment.candidate_dossier_id='forged';assert.throws(()=>validateOperations(input));
 input.autonomy_tasks[0].evidence_assessment.candidate_dossier_id='dossier-2';
 input.autonomy_tasks[0].evidence_assessment.resolution='RESOLVED';assert.throws(()=>validateOperations(input));
});
test('unknown task routing is visible but forged resolution route is rejected',()=>{
 const input=fixture();assert.equal(validateOperations(input).autonomy_tasks[0].effective_kind,'UNCLASSIFIED');
 input.autonomy_tasks[0].effective_kind='AUTO_RESOLVED';assert.throws(()=>validateOperations(input));
});
test('automatic research remains an unresolved local observation and stale verdicts cannot display',()=>{
 const input=fixture(),task=input.autonomy_tasks[0];
 task.research_evaluation={id:'RESEARCH-1',task_id:'TASK-1',availability:'CURRENT_INPUTS',scope:'ADMITTED_LOCAL_DOSSIERS_ONLY',verdict:'INSUFFICIENT',resolution:'NOT_RESOLVED',acceptance:'NOT_ACCEPTED',publication:'BLOCKED'};
 assert.equal(validateOperations(input).autonomy_tasks[0].state,'OPEN');
 task.research_evaluation.resolution='RESOLVED';assert.throws(()=>validateOperations(input));
 task.research_evaluation={id:'RESEARCH-1',task_id:'TASK-1',availability:'STALE_OR_REVOKED'};
 assert.equal(validateOperations(input).autonomy_tasks[0].research_evaluation.availability,'STALE_OR_REVOKED');
 task.research_evaluation.verdict='INSUFFICIENT';assert.throws(()=>validateOperations(input));
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

test('literal change context cannot escape currentness, lineage or causal limits',()=>{
 const input=fixture(),state=input.dossier_evidence[0];state.source_hash='a'.repeat(64);
 state.change_context={version:'0.1.0',scope:'LOCAL_LITERAL_CHANGE_CONTEXT',dossier_id:state.dossier_id,
  source_hash:state.source_hash,dossier_sha256:'b'.repeat(64),cause_certainty:'UNCONFIRMED',
  resolution:'NOT_RESOLVED',acceptance:'NOT_ACCEPTED',publication:'BLOCKED',
  facts:[{fact_id:'FACT-001',kind:'SAME_PERIOD_REPORTED_VALUE_CHANGE',unit:'THOUSAND_TONNES',geography:'BE',before_period:'2021',after_period:'2021'}]};
 assert.equal(validateOperations(input),input);
 assert.equal(changeContextLabel(state.change_context),'Valor reportado cambiado en el mismo periodo · causa no confirmada');
 for(const [key,value] of [['cause_certainty','VERIFIED'],['resolution','RESOLVED'],['publication','ALLOWED'],
                         ['source_hash','c'.repeat(64)],['dossier_id','forged']]) {
  const broken=structuredClone(input);broken.dossier_evidence[0].change_context[key]=value;
  assert.throws(()=>validateOperations(broken));
 }
 state.status='UNAVAILABLE';assert.throws(()=>validateOperations(input));
 state.change_context=null;assert.equal(validateOperations(input),input);
});
