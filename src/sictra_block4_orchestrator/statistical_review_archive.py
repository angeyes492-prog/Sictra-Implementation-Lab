"""Explicit candidate archival on the existing operations transaction plane."""
from contextlib import closing
from copy import deepcopy

from sictra_block1.research_admission import _time
from sictra_block1.statistical_dossier import StatisticalDossierProducer
from .operations_store import OperationsError, OperationsStore, encoded

KIND = "STATISTICAL_REVIEW_DOSSIER"


def _require(condition, reason):
    if not condition:
        raise OperationsError(reason)


class StatisticalReviewArchive:
    """Standalone explicit workflow; no installed scheduler or legacy adoption."""
    def __init__(self, *, store, producer, stopped, max_dossiers=100):
        _require(isinstance(store, OperationsStore) and isinstance(producer, StatisticalDossierProducer)
                 and callable(stopped) and type(max_dossiers) is int and 1 <= max_dossiers <= 100,
                 "STATISTICAL_ARCHIVE_CONFIGURATION_INVALID")
        source = producer.watchlist._store
        target = store.path.resolve()
        _require(target not in {source.path.resolve(), source._history.control.path.resolve()}
                 and target != source._history.quarantine.root.resolve()
                 and source._history.quarantine.root.resolve() not in target.parents,
                 "STATISTICAL_ARCHIVE_PATH_COLLISION")
        self.store, self.producer, self.stopped, self.capacity = store, producer, stopped, max_dossiers

    @staticmethod
    def _validate_record(value, identity, now):
        _require(type(value) is dict and set(value) == {"version", "recorded_at", "dossier"}
                 and value["version"] == "0.1.0" and type(value["recorded_at"]) is int
                 and 0 <= value["recorded_at"] <= now and type(value["dossier"]) is dict
                 and value["dossier"].get("dossier_id") == identity,
                 "STATISTICAL_ARCHIVE_RECORD_INVALID")

    def _guard(self, dossier, started):
        self.producer.verify_dossier(dossier)
        now = _time(self.producer.clock)
        _require(now >= started and now < dossier["expires_at"], "STATISTICAL_ARCHIVE_TIME_INVALID")
        _require(not self.stopped(), "STATISTICAL_ARCHIVE_STOPPED")
        return now

    def record(self):
        if self.stopped():
            return {"status": "STOPPED", "dossier_id": None, "replay": False}
        started = _time(self.producer.clock)
        dossier = self.producer.read()
        identity = dossier["dossier_id"]
        with closing(self.store.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            rows = [r for r in self.store._read(db) if r["kind"] == KIND]
            prior_row = next((r for r in reversed(rows) if r["identity"] == identity), None)
            now = self._guard(dossier, started)
            if prior_row is not None:
                prior = prior_row["value"]
                self._validate_record(prior, identity, now)
                _require(encoded(prior["dossier"]) == encoded(dossier), "STATISTICAL_ARCHIVE_IDENTITY_COLLISION")
            else:
                _require(len({r["identity"] for r in rows}) < self.capacity,
                         "STATISTICAL_ARCHIVE_CAPACITY_EXCEEDED")
                self.store._append(db, KIND, identity, {"version": "0.1.0", "recorded_at": now,
                                                      "dossier": dossier})
            self._guard(dossier, started)
            db.commit()
        return {"status": "JOURNALED_CANDIDATE", "dossier_id": identity, "replay": prior_row is not None,
                "resolution": "NOT_RESOLVED", "acceptance": "NOT_ACCEPTED", "publication": "BLOCKED"}

    def read(self, identity):
        _require(type(identity) is str and identity.startswith("STAT-DOSSIER-"),
                 "STATISTICAL_ARCHIVE_SELECTION_INVALID")
        started = _time(self.producer.clock)
        records = self.store.latest(KIND)
        _require(identity in records, "STATISTICAL_ARCHIVE_NOT_RETAINED")
        record = records[identity]
        self._validate_record(record, identity, started)
        self.producer.verify_dossier(record["dossier"])
        _require(encoded(record) == encoded(self.store.latest(KIND).get(identity)),
                 "STATISTICAL_ARCHIVE_CHANGED_DURING_READ")
        self.producer.verify_dossier(record["dossier"])
        now = _time(self.producer.clock)
        _require(now >= started and now < record["dossier"]["expires_at"],
                 "STATISTICAL_ARCHIVE_READ_EXPIRED")
        return {"availability": "CURRENT_INPUTS", "storage": "JOURNALED_CANDIDATE",
                "recorded_at": record["recorded_at"], "dossier": deepcopy(record["dossier"])}

    def editorial_candidate(self, identity):
        return self.producer.editorial_candidate(self.read(identity)["dossier"])
