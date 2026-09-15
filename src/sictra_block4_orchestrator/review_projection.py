"""Read-only, source-validated projections of local B2/B3 artifacts.

Candidate integration, not engine/gate acceptance. No controls, keys, source
acquisition or external delivery are exposed to these presentation consumers.
"""
from pathlib import Path
from .operations import OperationsService
from .operations_store import OperationsError
from .runtime import FederatedContractError
from sictra_block2_design.design_artifact import DesignArtifactError, render_designed_review_artifact
from sictra_block3_precision.audience_draft import AudiencePolicyError


def review_projection(root, block, *, clock=None):
    if block not in (2, 3):
        raise OperationsError('REVIEW_BLOCK_INVALID')
    result = {'scope':'LABORATORY_INTERNAL_SUPERVISED', 'block':block,
              'status':'NOT_CONFIGURED', 'artifacts':[], 'unavailable':[],
              'publication':'BLOCKED', 'acceptance':'NOT_ACCEPTED'}
    if root is None:
        return result
    root = Path(root).absolute()
    required = ('operations.sqlite','cases.sqlite','intake.sqlite','pipeline/pipeline-state.json')
    if any(p.is_symlink() for p in (root,*root.parents)) or any(not (root/name).is_file() for name in required):
        raise OperationsError('REVIEW_STATE_UNAVAILABLE')
    service = OperationsService(root, **({'clock':clock} if clock else {}))
    for identity in service.store.latest('OUTPUT'):
        try:
            value = service.output(identity)
            render_designed_review_artifact(value['design_artifact'], value['adaptation'])
        except (OperationsError,FederatedContractError,DesignArtifactError,AudiencePolicyError):
            result['unavailable'].append({'id':identity, 'reason':'STALE_REVOKED_OR_INVALID'})
            continue
        artifact = value['design_artifact']
        item = {'id':identity,'case_id':value['case_id'],'dossier_id':value['dossier_id'],
                'evidence_id':artifact['evidence_id'],'source_hash':artifact['source_hash'],
                'artifact_fingerprint':artifact['fingerprint'], 'state':value['state'],
                'title':value['adaptation']['heading'],'profile':value['profile']['label'],
                'publication':'BLOCKED', 'review':'HUMAN_REVIEW_REQUIRED',
                'content':artifact if block == 2 else value['adaptation']}
        result['artifacts'].append(item)
    result['status']='AVAILABLE'
    return result
