from __future__ import annotations

import copy
import csv
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.f0_candidate_handoff import HandoffError, main as handoff_main, render_model, validate_candidate, verify_handoff


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = json.loads((ROOT / "data/synthetic/system_model_candidate.json").read_text(encoding="utf-8"))
CLAIM = json.loads((ROOT / "data/synthetic/claim.json").read_text(encoding="utf-8"))
SOURCE = (ROOT / "data/synthetic/source.txt").read_text(encoding="utf-8")


class CandidateHandoffTests(unittest.TestCase):
    def test_candidate_resolves_source_claim_mechanism_and_assumptions(self):
        evidence = validate_candidate(CANDIDATE, CLAIM, SOURCE)
        self.assertEqual(evidence["source_claim_id"], CLAIM["claim_id"])
        self.assertEqual(evidence["quote"], CLAIM["quote"])
        self.assertEqual(evidence["quote_end"] - evidence["quote_start"], len(CLAIM["quote"]))

    def test_source_and_candidate_entity_types_are_required(self):
        candidate = copy.deepcopy(CANDIDATE)
        claim = copy.deepcopy(CLAIM)
        candidate["entity_type"] = "UnknownCandidate"
        with self.assertRaisesRegex(HandoffError, "SystemModelCandidate"):
            validate_candidate(candidate, claim, SOURCE)
        candidate = copy.deepcopy(CANDIDATE)
        claim["entity_type"] = "UnknownClaim"
        with self.assertRaisesRegex(HandoffError, "ClaimOccurrence"):
            validate_candidate(candidate, claim, SOURCE)

    def test_candidate_with_missing_flow_unit_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["structure"]["inflow"].pop("unit")
        with self.assertRaisesRegex(HandoffError, "unit"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_candidate_with_broken_assumption_reference_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["structure"]["outflow"]["assumption_id"] = "assumption-missing"
        with self.assertRaisesRegex(HandoffError, "undeclared assumption"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_mechanism_with_broken_claim_reference_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["mechanism_hypothesis"]["claim_id"] = "claim-missing"
        with self.assertRaisesRegex(HandoffError, "reference"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def test_flow_with_mismatched_parameter_name_is_rejected(self):
        candidate = copy.deepcopy(CANDIDATE)
        candidate["assumptions"][0]["parameter"] = "completionRate"
        with self.assertRaisesRegex(HandoffError, "parameter/unit"):
            validate_candidate(candidate, CLAIM, SOURCE)

    def _write_verification_fixture(self, root: Path) -> Path:
        source_dir = root / "data/synthetic"
        script_dir = root / "scripts"
        output_dir = root / "artifacts/f0/candidate-handoff"
        source_dir.mkdir(parents=True)
        script_dir.mkdir()
        output_dir.mkdir(parents=True)
        source_path = source_dir / "source.txt"
        claim_path = source_dir / "claim.json"
        candidate_path = source_dir / "system_model_candidate.json"
        generator_path = script_dir / "f0_candidate_handoff.py"
        source_path.write_text(SOURCE, encoding="utf-8")
        claim_path.write_text(json.dumps(CLAIM), encoding="utf-8")
        candidate_path.write_text(json.dumps(CANDIDATE), encoding="utf-8")
        generator_path.write_text("synthetic verifier source", encoding="utf-8")
        base_model = output_dir / "CandidateBase.mo"
        perturbed_model = output_dir / "CandidatePerturbed.mo"
        base_model.write_text(render_model(CANDIDATE, "CandidateBase"), encoding="utf-8")
        changed = copy.deepcopy(CANDIDATE)
        changed["assumptions"][0]["value"] = 4
        perturbed_model.write_text(render_model(changed, "CandidatePerturbed"), encoding="utf-8")
        base_csv = output_dir / "base_res.csv"
        perturbed_csv = output_dir / "perturbed_res.csv"
        for path, rows in (
            (base_csv, [(0, 0), (5, 10), (10, 20)]),
            (perturbed_csv, [(0, 0), (5, 15), (10, 30)]),
        ):
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["time", "orderStock"])
                writer.writerows(rows)
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {
            "schema": "igc-candidate-handoff-evidence/0.1",
            "status": "PASS_SYNTHETIC_INTEGRATION_ONLY",
            "synthetic": True,
            "source": {"path": str(source_path.relative_to(root)), "id": CLAIM["source_id"],
                       "sha256": digest(source_path)},
            "claim": {"path": str(claim_path.relative_to(root)), "id": CLAIM["claim_id"],
                      "entity_type": "ClaimOccurrence", "sha256": digest(claim_path)},
            "candidate": {"path": str(candidate_path.relative_to(root)),
                          "id": CANDIDATE["candidate_id"],
                          "entity_type": "SystemModelCandidate", "sha256": digest(candidate_path)},
            "generator": {"path": str(generator_path.relative_to(root)), "sha256": digest(generator_path)},
            "generated_models": {
                "base": {"path": str(base_model.relative_to(root)), "sha256": digest(base_model)},
                "perturbed": {"path": str(perturbed_model), "assumption_id": "assumption-arrival-rate-001",
                              "parameter": "arrivalRate", "before": 3, "after": 4, "delta": 1,
                              "sha256": digest(perturbed_model)},
            },
            "simulation": {
                "duration_hours": 10,
                "base_result": {"path": str(base_csv.relative_to(root)), "sha256": digest(base_csv),
                                "sample_count": 3, "final_stock": 20, "expected_final_stock": 20},
                "perturbed_result": {"path": str(perturbed_csv.relative_to(root)),
                                     "sha256": digest(perturbed_csv), "sample_count": 3,
                                     "final_stock": 30, "expected_final_stock": 30},
            },
        }
        manifest_path = output_dir / "handoff.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest_path

    def test_verify_handoff_rechecks_all_hashes_and_full_trajectories(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._write_verification_fixture(Path(directory))
            result = verify_handoff(manifest, root=Path(directory))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["sample_counts"], {"base": 3, "perturbed": 3})
        self.assertEqual(result["final_stock"], {"base": 20.0, "perturbed": 30.0})

    def test_verify_handoff_detects_modelica_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._write_verification_fixture(root)
            model = root / "artifacts/f0/candidate-handoff/CandidateBase.mo"
            model.write_text(model.read_text(encoding="utf-8") + "// changed\n", encoding="utf-8")
            with self.assertRaisesRegex(HandoffError, "base Modelica hash mismatch"):
                verify_handoff(manifest, root=root)

    def test_verify_handoff_detects_incorrect_interior_csv_sample_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = self._write_verification_fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            csv_path = root / manifest["simulation"]["perturbed_result"]["path"]
            csv_path.write_text("time,orderStock\n0,0\n5,13\n10,30\n", encoding="utf-8")
            manifest["simulation"]["perturbed_result"]["sha256"] = hashlib.sha256(
                csv_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(HandoffError, "trajectory mismatch"):
                verify_handoff(manifest_path, root=root)

    def test_verify_handoff_cli_reports_verified_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._write_verification_fixture(Path(directory))
            output = io.StringIO()
            with redirect_stdout(output):
                result = handoff_main(["verify-handoff", "--manifest", str(manifest)])
        self.assertEqual(result, 0)
        self.assertIn('"status": "PASS"', output.getvalue())

    def test_parameter_change_changes_generated_model(self):
        candidate = copy.deepcopy(CANDIDATE)
        base = render_model(candidate, "CandidateBase")
        candidate["assumptions"][0]["value"] += 1
        changed = render_model(candidate, "CandidatePerturbed")
        self.assertNotEqual(base, changed)
        self.assertIn("arrivalRate = 3", base)
        self.assertIn("arrivalRate = 4", changed)


if __name__ == "__main__":
    unittest.main()
