const test = require('node:test');
const assert = require('node:assert/strict');
const {stateInfo, filteredCases, validCases, escapeHTML} = require('../src/sictra_block4_orchestrator/command_center/app.js');
test('unknown states fail closed instead of implying human review', () => {
  assert.equal(stateInfo('BLOCK1_ATTESTED')[1], 'active');
  assert.equal(stateInfo('HUMAN_REVIEW_REQUIRED')[1], 'review');
  assert.equal(stateInfo('RETURN_UPSTREAM')[1], 'blocked');
  assert.equal(stateInfo('__proto__')[1], 'blocked');
});
test('case search combines execution identity and state without changing records', () => {
  const cases = Object.freeze([{case_id:'A',run_id:'RUN-1',state:'RETURN_UPSTREAM'}, {case_id:'B',run_id:'RUN-2',state:'HUMAN_REVIEW_REQUIRED'}]);
  assert.deepEqual(filteredCases(cases,' run-2 ', 'review').map(x=>x.case_id), ['B']);
  assert.equal(filteredCases(cases,'run-2','blocked').length,0);
  assert.equal(cases.length,2);
});
test('malformed responses cannot masquerade as an empty successful read', () => {
  assert.deepEqual(validCases({cases:[],authority:{acceptance:'NOT_ACCEPTED'}}), []);
  for (const payload of [{}, {cases:[]}, {cases:[],authority:{acceptance:'APPROVED'}}, {cases:[null],authority:{acceptance:'NOT_ACCEPTED'}}]) assert.throws(()=>validCases(payload));
});
test('untrusted identifiers and audit content are escaped', () => {
  assert.equal(escapeHTML('<img src=x onerror="x">'), '&lt;img src=x onerror=&quot;x&quot;&gt;');
});
