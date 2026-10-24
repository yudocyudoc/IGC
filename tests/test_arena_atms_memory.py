"""Adversarial contracts for Arena shared ATMS/memory (synthetic only)."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.arena_atms import ATMS, ATMSError, ATMSLimitError, Rule, digest, project
from scripts.arena_memory import retrieve, load_events_from_ledger
from scripts.ledger import Ledger


AT = "2026-10-20T10:00:00Z"
AFTER = "2026-10-21T10:00:00Z"
RESTORED = "2026-10-22T10:00:00Z"


def event(kind, identifier, at=AT, policy="construction-visible", active=True, **fields):
    return dict(kind=kind, id=identifier, recorded_at=at,
                access_policy=policy, active=active, **fields)


def base_events():
    return [
        event("assumption", "mechanism"),
        event("assumption", "evidence-a"),
        event("assumption", "evidence-b"),
        event("assumption", "afluencia"),
        event("justification", "j-a", antecedents=["mechanism", "evidence-a"],
              consequent="H-ESPERA", source_id="S-a"),
        event("justification", "j-b", antecedents=["mechanism", "evidence-b"],
              consequent="H-ESPERA", source_id="S-b"),
        event("justification", "j-c", antecedents=["afluencia"],
              consequent="H-AFLUENCIA", source_id="S-c")
    ]


def knowledge():
    return [
        event("knowledge", "k-wait", investigation_id="INV-CAF-001",
              title="Abandono por espera", text="Hipótesis cualitativa de clientes en espera",
              node_id="H-ESPERA", source_id="S-a", item_type="hypothesis"),
        event("knowledge", "k-arrivals", investigation_id="INV-CAF-001",
              title="Menor afluencia", text="Hipótesis rival por menor llegada",
              node_id="H-AFLUENCIA", source_id="S-c", item_type="hypothesis"),
        event("knowledge", "k-gold", investigation_id="INV-CAF-001",
              title="Abandono por espera - verdad oculta",
              text="H-ESPERA fue la generadora",
              node_id="hidden-model", source_id="GOLD",
              policy="evaluation-only", item_type="gold"),
        event("knowledge", "k-future", at=AFTER,
              investigation_id="INV-CAF-001",
              title="Abandono por espera posterior",
              text="Dato futuro", node_id="future", source_id="S-future")
    ]


class AtmsEngineTests(unittest.TestCase):
    def test_alternatives_and_minimal_labels(self):
        engine, _ = project(base_events(), as_known_at=AT, lane="D")
        self.assertEqual(engine.explain("H-ESPERA")["minimal_environments"],
                         [["evidence-a", "mechanism"], ["evidence-b", "mechanism"]])
        self.assertTrue(engine.supported_in("H-ESPERA", {"mechanism", "evidence-a"}))
        self.assertFalse(engine.supported_in("H-ESPERA", {"mechanism"}))

    def test_nogood_prunes_one_path_not_candidate(self):
        engine, _ = project(base_events() + [
            event("nogood", "contradiction", assumption_ids=["mechanism", "evidence-a"])
        ], as_known_at=AT, lane="S")
        self.assertEqual(engine.explain("H-ESPERA")["minimal_environments"],
                         [["evidence-b", "mechanism"]])
        self.assertTrue(engine.explain("H-AFLUENCIA")["supported"])

    def test_no_unfounded_cyclic_support(self):
        engine = ATMS(set(), set(), [Rule("a", ("q",), "p"),
                                      Rule("b", ("p",), "q")], set())
        self.assertFalse(engine.explain("p")["supported"])
        self.assertFalse(engine.explain("q")["supported"])

    def test_grounded_cycle_explains_without_recursion(self):
        engine = ATMS({"a"}, set(), [Rule("root", ("a",), "p"),
                                      Rule("loop1", ("p",), "q"),
                                      Rule("loop2", ("q",), "p")], set())
        self.assertTrue(engine.explain("q")["supported"])
        self.assertEqual(engine.explain("q")["paths"][0]["via"], "loop1")

    def test_logical_retraction_and_restoration_keep_prior_snapshot(self):
        events = base_events() + [
            event("assumption", "evidence-a", at=AFTER, active=False),
            event("assumption", "evidence-a", at=RESTORED, active=True)
        ]
        old, _ = project(events, as_known_at=AT, lane="D")
        middle, _ = project(events, as_known_at=AFTER, lane="D")
        new, _ = project(events, as_known_at=RESTORED, lane="D")
        self.assertEqual(len(old.explain("H-ESPERA")["minimal_environments"]), 2)
        self.assertEqual(middle.explain("H-ESPERA")["minimal_environments"],
                         [["evidence-b", "mechanism"]])
        self.assertEqual(old.to_report()["labels"], new.to_report()["labels"])

    def test_justification_retraction_restoration(self):
        events = base_events() + [
            event("justification", "j-a", at=AFTER, active=False,
                  antecedents=["mechanism", "evidence-a"], consequent="H-ESPERA"),
            event("justification", "j-a", at=RESTORED, active=True,
                  antecedents=["mechanism", "evidence-a"], consequent="H-ESPERA")
        ]
        a, _ = project(events, as_known_at=AFTER, lane="D")
        b, _ = project(events, as_known_at=RESTORED, lane="D")
        self.assertEqual(len(a.explain("H-ESPERA")["paths"]), 1)
        self.assertEqual(len(b.explain("H-ESPERA")["paths"]), 2)

    def test_why_includes_chain_to_atomic_assumptions(self):
        engine, _ = project(base_events(), as_known_at=AT, lane="P")
        paths = engine.explain("H-ESPERA")["paths"]
        self.assertEqual({x["via"] for x in paths}, {"j-a", "j-b"})
        self.assertEqual({leaf["node"] for path in paths for leaf in path["premises"]},
                         {"mechanism", "evidence-a", "evidence-b"})

    def test_budgets_fail_explicitly(self):
        with self.assertRaisesRegex(ATMSLimitError, "COMBINATORIAL_LIMIT_REACHED"):
            ATMS({"a", "b"}, set(), [Rule("or1", ("a",), "h"),
                                     Rule("or2", ("b",), "h")], set(), max_environments=1)

    def test_extra_nogood_superset_is_minimized(self):
        a = ATMS({"a", "b"}, set(), [], {frozenset({"a"}), frozenset({"a", "b"})})
        self.assertEqual(a.to_report()["nogoods"], [["a"]])

    def test_same_events_deterministic_hash(self):
        one, m1 = project(base_events(), as_known_at=AT, lane="D")
        two, m2 = project(list(reversed(base_events())), as_known_at=AT, lane="D")
        self.assertEqual(one.to_report(), two.to_report())
        self.assertEqual(m1["projection_hash"], m2["projection_hash"])


class RetrievalTests(unittest.TestCase):
    def test_retrieves_hypotheses_with_support_not_just_documents(self):
        packet = retrieve(investigation_id="INV-CAF-001", lane="D",
                          as_known_at=AT, query="abandono espera",
                          knowledge_records=knowledge(), atms_events=base_events())
        self.assertEqual([x["id"] for x in packet["items"]], ["k-wait"])
        self.assertEqual(len(packet["items"][0]["logical_support"]["paths"]), 2)
        self.assertEqual(packet["items"][0]["truth_status"], "NOT_DETERMINED_BY_ATMS")
        self.assertEqual(packet["vector_backend_status"], "NOT_IMPLEMENTED")

    def test_no_future_gold_or_other_case_leak(self):
        extra = knowledge() + [event("knowledge", "other", investigation_id="OTHER",
                                    title="Abandono espera", text="secreto",
                                    node_id="H-ESPERA", source_id="other")]
        packet = retrieve(investigation_id="INV-CAF-001", lane="D", as_known_at=AT,
                          query="abandono espera", knowledge_records=extra,
                          atms_events=base_events() + [
                              event("assumption", "hidden", policy="evaluation-only"),
                              event("justification", "secret-rule",
                                    antecedents=["hidden"], consequent="H-ESPERA",
                                    policy="evaluation-only")
                          ])
        encoded = json.dumps(packet)
        for forbidden in ("GOLD", "Dato futuro", "secreto", "hidden", "secret-rule", "k-future"):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(packet["coverage"]["authorized_knowledge_items"], 2)

    def test_lane_isolation_with_same_atms_service(self):
        private = [event("assumption", "secretS", policy="lane:S"),
                   event("justification", "secretJ", policy="lane:S",
                         antecedents=["secretS"], consequent="H-ESPERA")]
        d, _ = project(base_events() + private, as_known_at=AT, lane="D")
        s, _ = project(base_events() + private, as_known_at=AT, lane="S")
        self.assertNotIn("secretS", json.dumps(d.to_report()))
        self.assertIn("secretS", json.dumps(s.to_report()))

    def test_hidden_revision_overrides_visible_old_version_without_leak(self):
        items = knowledge() + [event("knowledge", "k-wait", at=AFTER, policy="evaluation-only",
                                    investigation_id="INV-CAF-001",
                                    title="Abandono por espera", text="reservado",
                                    node_id="H-ESPERA", source_id="secret")]
        packet = retrieve(investigation_id="INV-CAF-001", lane="D", as_known_at=AFTER,
                          query="hipotesis cualitativa", knowledge_records=items,
                          atms_events=base_events())
        self.assertEqual(packet["items"], [])

    def test_lexical_ranking_is_reproducible(self):
        params = dict(investigation_id="INV-CAF-001", lane="D", as_known_at=AT,
                      query="hipotesis", knowledge_records=knowledge(),
                      atms_events=base_events())
        a, b = retrieve(**params), retrieve(**params)
        self.assertEqual(a["reproducibility_hash"], b["reproducibility_hash"])


class LedgerIntegrationTests(unittest.TestCase):
    def test_append_only_atms_snapshots_and_knowledge_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "ledger.sqlite"
            migration = Path(__file__).resolve().parents[1] / "migrations/0001_ledger.sql"
            ledger = Ledger(db, migration)
            for n, (kind, payload) in enumerate([
                ("Assumption", {"kind": "assumption", "active": True}),
                ("KnowledgeItem", {"title": "Cola y espera", "text": "Hipótesis",
                                    "node_id": "h", "source_id": "S1",
                                    "epistemic_status": "HIPOTESIS"}),
                ("Justification", {"kind": "justification", "active": True,
                                    "antecedents": ["a"], "consequent": "h"})
            ]):
                ledger.append_revision(entity_id=("a", "k", "j")[n],
                    entity_type=kind, case_id="INV-1", actor_id="tester",
                    idempotency_key=f"test-{n}", payload=payload,
                    recorded_at=AT, created_at=AT, access_policy="construction-visible")
            k, atms = load_events_from_ledger(db, "INV-1", AT)
            packet = retrieve(investigation_id="INV-1", lane="D", as_known_at=AT,
                              query="cola espera", knowledge_records=k, atms_events=atms)
            self.assertEqual(len(packet["items"]), 1)
            self.assertEqual(packet["items"][0]["logical_support"]["minimal_environments"], [["a"]])


if __name__ == "__main__":
    unittest.main()
