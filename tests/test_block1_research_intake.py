"""Behavioral and adversarial tests for local operator research intake."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sictra_block1.research_intake import ResearchIntakeStore, ResearchIntakeViolation


def payload(**overrides):
    value = {
        "title": "Riesgo de reposición electrónica",
        "question": "¿Qué señales deben investigarse antes de revisar la reposición?",
        "level": "REGIONAL",
        "geography": "China a México",
        "industry": "electronics",
        "actor": "Importadores",
        "mode": "Marítimo y terrestre",
        "period": "30 días",
        "topic_keys": ["supply_chain_resilience", "port_congestion"],
        "source_reference": "https://example.test/report",
    }
    value.update(overrides)
    return value


class ResearchIntakeStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "intake.json"
        self.store = ResearchIntakeStore(
            self.path,
            clock=lambda: "2026-09-05T00:00:00Z",
            id_factory=lambda: "draft-test-0001",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_is_durable_and_never_mints_evidence(self):
        draft = self.store.create(payload())
        self.assertEqual(draft["status"], "DRAFT")
        self.assertEqual(draft["certainty"], "INSUFFICIENT EVIDENCE")
        self.assertEqual(draft["confidence"], "E")
        self.assertEqual(draft["sources"], [])
        self.assertEqual(draft["claims"], [])
        self.assertEqual(draft["strategies"], [])
        self.assertEqual(
            draft["operator_declaration"]["status"], "NOT_FETCHED_NOT_EVIDENCE"
        )
        reopened = ResearchIntakeStore(self.path).list()
        self.assertEqual(reopened, [draft])
        reopened[0]["title"] = "mutated"
        self.assertEqual(self.store.list()[0]["title"], draft["title"])

    def test_rejects_unknown_topics_wrong_shape_and_noncontrolled_industry(self):
        for candidate in (
            payload(topic_keys=["made_up_topic"]),
            payload(industry="uncontrolled"),
            {"title": "incomplete"},
        ):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ResearchIntakeViolation):
                    self.store.create(candidate)

    def test_corrupted_durable_record_fails_closed(self):
        self.store.create(payload())
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        raw["records"][0]["certainty"] = "VERIFIED"
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(ResearchIntakeViolation):
            self.store.list()


if __name__ == "__main__":
    unittest.main()
