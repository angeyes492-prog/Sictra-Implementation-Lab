"""Read-only facts about a current local editorial candidate."""
from hashlib import sha256
from datetime import datetime, timezone
from html import escape
import json
import re

from .operations_store import OperationsError, encoded
from sictra_block2_design.design_artifact import render_designed_review_artifact


def build_factsheet(service, identity):
    if not isinstance(identity, str) or not re.fullmatch(r'[a-f0-9]{64}', identity):
        raise OperationsError('FACTSHEET_ID_INVALID')
    with service.lock:
        value = service.output(identity)
        design, adaptation = value['design_artifact'], value['adaptation']
        html, plain = render_designed_review_artifact(design, adaptation)
        if (html != value['html'] or plain != value['plain_text']
                or sha256(html.encode()).hexdigest() != value['html_sha256']):
            raise OperationsError('FACTSHEET_CONTENT_MISMATCH')
        records = service.store.records()
        latest = lambda kind: {r['identity']: r['value'] for r in records if r['kind'] == kind}
        deferred = [v for v in latest('DEFERRED_REVIEW').values() if v['dossier_id'] == value['dossier_id']]
        result = {
            'schema': 'TELECARE_FACTSHEET_V1', 'scope': 'LABORATORY_INTERNAL_SUPERVISED',
            'observed_at': int(service.clock()), 'id': identity, 'case_id': value['case_id'],
            'dossier_id': value['dossier_id'], 'created_at': value['created_at'],
            'title': adaptation['heading'],
            'data_class': latest('ENV').get('data', {}).get('class', 'OPERATOR_SUPPLIED_FILES'),
            'source': {k: design[k] for k in ('source_hash', 'evidence_id', 'source_id', 'expires_at')},
            'source_hash_scope': 'CANONICAL_MAPPED_CONTENT',
            'design': {'fingerprint': design['fingerprint'], 'artifact_type': design['artifact_type'], 'version': design['version']},
            'uncertainty': [b['body'] for b in design['content_blocks'] if b['kind'] in ('UNCERTAINTY', 'EVIDENCE_GAP', 'LIMITATION')],
            'audience': {'id': value['profile']['id'], 'label': value['profile']['label'],
                         'profile_sha256': sha256(encoded(value['profile'])).hexdigest(),
                         'adaptation_sha256': sha256(encoded(adaptation)).hexdigest()},
            'html_sha256': value['html_sha256'], 'stages': value['stages'],
            'review': value['review'], 'deferred_reviews': deferred,
            'recovery_scope': 'STORE_HISTORY_NOT_ARTIFACT_EXECUTION',
            'store_recovery_count': len(latest('RECOVERY')),
            'validation': {'current_source_and_profile': True, 'design_binding': True,
                           'artifact_tests': 'NOT_ATTACHED', 'independent_review': 'NOT_ATTACHED'},
            'publication': 'BLOCKED', 'delivery': 'NONE', 'acceptance': 'NOT_ACCEPTED',
            'limits': ['Valid only at observed_at; revalidate before use.',
                       'Technical change is not causal or commercial insight.',
                       'Copy checksum is not an authenticity signature.'],
        }
        # A mutable source/profile may change while constructing the projection.
        if service.output(identity) != value:
            raise OperationsError('FACTSHEET_CHANGED_DURING_READ')
        result['sha256'] = sha256(encoded(result)).hexdigest()
        return result


def render_factsheet(value):
    def e(text):
        return escape(str(text), quote=True)
    labels = {'BLOCK1_DOSSIER_VERIFIED': 'Intelligence · dossier retenido y verificado',
              'BLOCK2_CONTENT_DESIGN': 'Design · composición del boletín',
              'BLOCK3_AUDIENCE_ADAPTATION': 'Precision · adaptación al perfil declarado'}
    stages = ''.join('<li>' + e(labels.get(stage, stage)) + '</li>' for stage in value['stages'])
    date = lambda stamp: datetime.fromtimestamp(stamp, timezone.utc).strftime('%d/%m/%Y %H:%M UTC')
    rows = [('Dossier', value['dossier_id']), ('Evidencia', value['source']['evidence_id']),
            ('Huella del contenido normalizado', value['source']['source_hash']), ('Audiencia', value['audience']['label']),
            ('Clase de datos', 'Prueba sintética' if value['data_class'] == 'SYNTHETIC_PILOT' else 'Archivos aportados por el operador'),
            ('Creado', date(value['created_at'])), ('Lectura', date(value['observed_at'])),
            ('Estado de revisión', 'Revisión humana pendiente'),
            ('Revisiones diferidas de este dossier', len(value['deferred_reviews'])),
            ('Recuperaciones del almacén', value['store_recovery_count'])]
    details = ''.join('<dt>' + e(k) + '</dt><dd>' + e(v) + '</dd>' for k, v in rows)
    return ('<!doctype html><html lang="es"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Ficha de trazabilidad</title><style>'
            'body{font:15px/1.6 system-ui;color:#213349;background:#f4f7fb;margin:0;padding:28px}'
            'main{max-width:780px;margin:auto;background:white;padding:28px;border-radius:20px}'
            'h1{font-size:25px;line-height:1.3}dt{font-weight:600;margin-top:16px}'
            'dd{margin:0;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}'
            '</style><main><p>Telecare OS · Ficha de trazabilidad</p><h1>' + e(value['title']) + '</h1>'
            '<p>Publicación bloqueada · lectura local · contenido no aceptado</p>'
            '<h2>Recorrido del boletín</h2><ol>' + stages + '</ol><dl>' + details + '</dl>'
            '<p>La vigencia corresponde al momento de esta lectura. Las recuperaciones son del almacén. '
            'Las pruebas del software y la revisión independiente no están adjuntas a este boletín.</p>'
            '<details><summary>Contrato completo y huella de la copia</summary><pre>'
            + e(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre></details></main></html>')
