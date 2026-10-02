"""Bounded, durable research over admitted local dossiers; no task promotion."""

from datetime import datetime
from hashlib import sha256

from .operations_store import OperationsError, encoded
from .runtime import FederatedContractError


def _digest(value):
    return sha256(encoded(value)).hexdigest()


def _source(value):
    return {key: data for key, data in value.items() if key != "checked_at"}


def _within_expiry(source, candidate, now):
    for evidence in (source, candidate):
        if evidence is None:
            continue
        try:
            expiry = datetime.fromisoformat(evidence["expires_at"])
            if expiry.tzinfo is None or expiry.timestamp() <= now:
                return False
        except (KeyError, TypeError, ValueError):
            return False
    return True


class LocalResearchCycle:
    def __init__(self, *, store, source_check, candidate_check, clock, stopped):
        self.store, self.source_check, self.candidate_check = store, source_check, candidate_check
        self.clock, self.stopped = clock, stopped

    def _body(self, task, source, candidate, inventory):
        assessment = candidate["assessment"] if candidate else None
        return {
            "version": "0.1.0", "scope": "ADMITTED_LOCAL_DOSSIERS_ONLY",
            "task_id": task["task_id"], "requirement_sha256": _digest([task["source_id"], task["requirement"]]),
            "source": _source(source), "candidate": candidate,
            "inventory_sha256": None if candidate else inventory,
            "inventory_boundary": "OBSERVED_CYCLE_SNAPSHOT",
            "verdict": assessment["verdict"] if assessment else "WAITING_LOCAL_EVIDENCE",
            "reason_code": assessment["reason_code"] if assessment else "NO_DISTINCT_ROOT_LOCAL_CANDIDATE",
            "next_action": assessment["next_action"] if assessment else "PROVIDE_APPROVED_LOCAL_EVIDENCE",
            "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED", "publication": "BLOCKED",
        }

    def run(self, tasks, dossiers, *, budget=8):
        if type(budget) is not int or not 1 <= budget <= 32:
            raise OperationsError("RESEARCH_BUDGET_INVALID")
        if self.stopped():
            return []
        inventory = _digest(sorted((d["dossier_id"], d["source"]["content_sha256"]) for d in dossiers))
        current_ids = {d["dossier_id"] for d in dossiers}
        work = []
        for task in sorted(tasks, key=lambda item: item["task_id"]):
            if task["dossier_id"] not in current_ids:
                continue
            candidates = sorted((d for d in dossiers
                if d["dossier_id"] != task["dossier_id"] and
                d["source"].get("root_source_identity", d["source"]["source_id"]) != task["source_root"]),
                key=lambda item: item["dossier_id"])
            work.extend((task, d["dossier_id"]) for d in candidates)
            if not candidates:
                work.append((task, None))
        if not work:
            return []
        cursor = self.store.latest("CURSOR").get("research", {}).get("position", 0) % len(work)
        batch = (work[cursor:] + work[:cursor])[:budget]
        outcomes = []
        processed = 0
        for task, candidate_id in batch:
            if self.stopped():
                break
            processed += 1
            source = self.source_check(task["dossier_id"])
            if source["status"] != "CURRENT":
                continue
            try:
                candidate = self.candidate_check(task, candidate_id) if candidate_id else None
                # Revalidate both identities and currentness immediately before persistence.
                current_source = self.source_check(task["dossier_id"])
                if _source(current_source) != _source(source) or current_source["status"] != "CURRENT":
                    continue
                if candidate_id and self.candidate_check(task, candidate_id) != candidate:
                    continue
                final_source = self.source_check(task["dossier_id"])
                if final_source["status"] != "CURRENT" or _source(final_source) != _source(source):
                    continue
            except (OperationsError, FederatedContractError):
                continue
            if self.stopped():
                break
            evaluated_at = int(self.clock())
            if not _within_expiry(source, candidate, evaluated_at):
                continue
            body = self._body(task, source, candidate, inventory)
            identity = "RESEARCH-" + _digest(body)
            prior = self.store.latest("RESEARCH_EVALUATION").get(identity)
            if prior is not None:
                if {k: v for k, v in prior.items() if k not in {"id", "evaluated_at"}} != body:
                    raise OperationsError("RESEARCH_EVALUATION_COLLISION")
                result = prior
            else:
                result = {**body, "id": identity, "evaluated_at": evaluated_at}
            self.store.put_batch([
                ("RESEARCH_EVALUATION", identity, result, True),
                ("RESEARCH_HEAD", task["task_id"], {"evaluation_id": identity}, False),
            ])
            outcomes.append({"id": identity, "task_id": task["task_id"], "verdict": result["verdict"]})
        if not self.stopped():
            self.store.put("CURSOR", "research", {"position": (cursor + processed) % len(work)})
        return outcomes

    def view(self, task):
        head = self.store.latest("RESEARCH_HEAD").get(task["task_id"])
        if head is None:
            return None
        identity = head.get("evaluation_id")
        result = self.store.latest("RESEARCH_EVALUATION").get(identity)
        rejected = {"id": identity, "task_id": task["task_id"], "availability": "STALE_OR_REVOKED"}
        if not isinstance(result, dict):
            return rejected
        try:
            source = self.source_check(task["dossier_id"])
            if source["status"] != "CURRENT":
                return rejected
            candidate = (self.candidate_check(task, result["candidate"]["dossier_id"])
                         if result.get("candidate") else None)
            final_source = self.source_check(task["dossier_id"])
            if final_source["status"] != "CURRENT" or _source(final_source) != _source(source):
                return rejected
            if not _within_expiry(source, candidate, int(self.clock())):
                return rejected
            body = self._body(task, source, candidate, result.get("inventory_sha256"))
            if (identity != "RESEARCH-" + _digest(body) or result.get("id") != identity
                    or {k: v for k, v in result.items() if k not in {"id", "evaluated_at"}} != body):
                return rejected
        except (OperationsError, FederatedContractError, KeyError, TypeError):
            return rejected
        return {**result, "availability": "CURRENT_INPUTS"}
