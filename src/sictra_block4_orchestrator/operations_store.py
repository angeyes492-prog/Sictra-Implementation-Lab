"""Durable append-only local operations records and verifiable backups."""
from contextlib import contextmanager, closing
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import sqlite3


class OperationsError(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def atomic_write(path, content):
    temporary = path.with_name(path.name + ".tmp-" + os.urandom(8).hex())
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def process_lock(path):
    """OS releases this advisory single-writer lock even on a process crash."""
    with Path(path).open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise OperationsError("SERVICE_ALREADY_RUNNING") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class OperationsStore:
    def __init__(self, path, key):
        self.path, self.key = Path(path), key
        if not isinstance(key, bytes) or len(key) < 32 or self.path.is_symlink():
            raise OperationsError("OPERATIONS_STORE_CONFIGURATION_INVALID")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists()
        with closing(self.connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS records (seq INTEGER PRIMARY KEY, kind TEXT, identity TEXT, body TEXT, previous TEXT, signature TEXT)")
            if not exists:
                self._append(db, "GENESIS", "operations-v1", {"version": 1})
            self._read(db)
            db.commit()

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def _read(self, db):
        previous, result = "GENESIS", []
        for index, row in enumerate(db.execute("SELECT seq,kind,identity,body,previous,signature FROM records ORDER BY seq"), 1):
            seq, kind, identity, body, prior, signature = row
            expected = hmac.new(self.key, encoded([seq, kind, identity, body, previous]), "sha256").hexdigest()
            if seq != index or prior != previous or not hmac.compare_digest(expected, signature):
                raise OperationsError("OPERATIONS_INTEGRITY_ERROR")
            result.append({"seq": seq, "kind": kind, "identity": identity, "value": json.loads(body)})
            previous = signature
        if not result or result[0]["kind"] != "GENESIS":
            raise OperationsError("OPERATIONS_GENESIS_MISSING")
        return result

    def _append(self, db, kind, identity, value):
        last = db.execute("SELECT seq,signature FROM records ORDER BY seq DESC LIMIT 1").fetchone()
        seq, previous = (last[0] + 1, last[1]) if last else (1, "GENESIS")
        body = encoded(value).decode()
        if len(body) > 2_000_000:
            raise OperationsError("RECORD_SIZE_EXCEEDED")
        signature = hmac.new(self.key, encoded([seq, kind, identity, body, previous]), "sha256").hexdigest()
        db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)", (seq, kind, identity, body, previous, signature))

    def records(self):
        with closing(self.connect()) as db:
            db.execute("BEGIN")
            return self._read(db)

    def put(self, kind, identity, value, *, immutable=False):
        with closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            records = self._read(db)
            prior = next((x for x in reversed(records) if x["kind"] == kind and x["identity"] == identity), None)
            if prior and prior["value"] == value:
                return False
            if immutable and prior:
                raise OperationsError("IMMUTABLE_IDENTITY_COLLISION")
            self._append(db, kind, identity, value)
            db.commit()
            return True

    def latest(self, kind):
        return {x["identity"]: x["value"] for x in self.records() if x["kind"] == kind}

    def backup(self, directory):
        target = Path(directory)
        if target.exists() or target.is_symlink():
            raise OperationsError("BACKUP_TARGET_EXISTS")
        self.records()
        target.mkdir(parents=True)
        path = target / "operations.sqlite"
        with closing(self.connect()) as source, closing(sqlite3.connect(path)) as destination:
            source.backup(destination)
        manifest = {"version": 1, "scope": "OPERATIONS_ONLY", "sha256": sha256(path.read_bytes()).hexdigest(),
                    "keys_included": False, "source_pipeline_included": False}
        manifest["signature"] = hmac.new(self.key, encoded(manifest), "sha256").hexdigest()
        (target / "manifest.json").write_bytes(encoded(manifest))
        self.verify_backup(target)
        return manifest

    def verify_backup(self, directory):
        target = Path(directory)
        paths = (target, target / "manifest.json", target / "operations.sqlite")
        if any(p.is_symlink() for p in paths):
            raise OperationsError("BACKUP_PATH_INVALID")
        manifest = json.loads(paths[1].read_text(encoding="utf-8"))
        signature = manifest.pop("signature", None)
        expected = hmac.new(self.key, encoded(manifest), "sha256").hexdigest()
        if (not isinstance(signature, str) or not hmac.compare_digest(signature, expected)
                or manifest.get("sha256") != sha256(paths[2].read_bytes()).hexdigest()):
            raise OperationsError("BACKUP_INTEGRITY_ERROR")
        with closing(sqlite3.connect(paths[2])) as db:
            self._read(db)
        return manifest

    def restore(self, directory, destination):
        self.verify_backup(directory)
        target = Path(destination)
        if target.exists() or target.is_symlink():
            raise OperationsError("RESTORE_TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((Path(directory) / "operations.sqlite").read_bytes())
        return OperationsStore(target, self.key)
