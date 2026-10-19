import json
import tempfile
import unittest
from pathlib import Path

from scripts.lock_from_pip_report import render_lock
from scripts.f0_atms_probe import AtmsProbe, run_atms_probe
from scripts.sbom_from_lock import render_spdx
from scripts.sbom_from_inventory import render_platform_spdx
from scripts.f0_spike import overall_status, run_semantic_pipeline, source_and_annotation


class F0SpikeContractTests(unittest.TestCase):

    def test_platform_sbom_includes_runner_container_actions_and_python(self):
        digest = "b" * 64
        commit = "a" * 40
        lock_text = (
            "# synthetic lock\n"
            "demo-pkg==2.0.0 \\\n"
            f"    --hash=sha256:{digest}\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / "requirements.lock"
            lock.write_text(lock_text, encoding="utf-8")
            runner = root / "runner.tsv"
            runner.write_text("libc\t2.0\tamd64\n", encoding="utf-8")
            container = root / "container.tsv"
            container.write_text("omc-lib\t1.0\tamd64\n", encoding="utf-8")
            workflow = root / "workflow.yml"
            workflow.write_text(
                f"      uses: actions/checkout@{commit} # v6\n"
                f"      uses: actions/setup-python@{commit} # v7\n"
                f"      uses: actions/upload-artifact@{commit} # v4\n",
                encoding="utf-8",
            )
            document = render_platform_spdx(
                lock, runner, container, workflow, "ubuntu-24.04",
                "openmodelica/openmodelica:v1.27.1-minimal",
                "sha256:" + "c" * 64,
            )
        scopes = [package["SPDXID"].split("-")[1] for package in document["packages"]]
        self.assertEqual(len(document["packages"]), 8)
        self.assertTrue(all(package["licenseDeclared"] == "NOASSERTION"
                            for package in document["packages"]))
        self.assertIn("runner", document["comment"])
        self.assertIn("OpenModelica image", document["comment"])
        self.assertIn("3 pinned GitHub Actions", document["comment"])


    def test_platform_sbom_includes_pinned_modelica_source(self):
        digest = "d" * 64
        commit = "a" * 40
        lock_text = (
            "demo-pkg==2.0.0 \\\n"
            f"    --hash=sha256:{digest}\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / "requirements.lock"
            lock.write_text(lock_text, encoding="utf-8")
            runner = root / "runner.tsv"
            runner.write_text("libc\t2.0\tamd64\n", encoding="utf-8")
            container = root / "container.tsv"
            container.write_text("omc-lib\t1.0\tamd64\n", encoding="utf-8")
            workflow = root / "workflow.yml"
            workflow.write_text(f"      uses: actions/checkout@{commit} # v6\n", encoding="utf-8")
            extras = root / "extras.json"
            extras.write_text(json.dumps([{
                "name": "SystemDynamics",
                "version": "2.1.2+b986a2ea354ab550d627a392f857ad7c9997d961",
                "scope": "modelica-source",
                "purl": "pkg:github/modelica-3rdparty/SystemDynamics@b986a2ea354ab550d627a392f857ad7c9997d961",
                "downloadLocation": "https://github.com/modelica-3rdparty/SystemDynamics/archive/b986a2ea354ab550d627a392f857ad7c9997d961.tar.gz",
                "checksums": [{"algorithm": "SHA256", "checksumValue": "e" * 64}],
                "comment": "Pinned upstream source snapshot.",
            }]), encoding="utf-8")
            document = render_platform_spdx(
                lock, runner, container, workflow, "ubuntu-24.04",
                "openmodelica/openmodelica:v1.27.1-minimal",
                "sha256:" + "c" * 64, extras,
            )
        package = next(item for item in document["packages"] if item["name"] == "SystemDynamics")
        self.assertIn("2.1.2+b986a2ea", package["versionInfo"])
        self.assertEqual(package["checksums"][0]["checksumValue"], "e" * 64)
        self.assertIn("additional package records: 1", document["comment"])
        namespace_with_extra = document["documentNamespace"]
        with tempfile.TemporaryDirectory() as changed_directory:
            changed_extras = Path(changed_directory) / "extras.json"
            changed_record = json.loads(json.dumps({
                "name": "SystemDynamics",
                "version": "2.1.2+" + "a" * 40,
                "scope": "modelica-source",
                "purl": "pkg:github/modelica-3rdparty/SystemDynamics@" + "a" * 40,
                "downloadLocation": "https://example.invalid/SystemDynamics.tar.gz",
                "checksums": [{"algorithm": "SHA256", "checksumValue": "f" * 64}],
                "comment": "Changed package manifest.",
            }))
            changed_extras.write_text(json.dumps([changed_record]), encoding="utf-8")
            changed = render_platform_spdx(
                lock, runner, container, workflow, "ubuntu-24.04",
                "openmodelica/openmodelica:v1.27.1-minimal",
                "sha256:" + "c" * 64, changed_extras,
            )
        self.assertNotEqual(namespace_with_extra, changed["documentNamespace"])

    def test_sbom_contains_lock_hash_and_unasserted_license(self):
        digest = "b" * 64
        lock_text = (
            "# synthetic lock\n"
            "demo-pkg==2.0.0 \\\n"
            f"    --hash=sha256:{digest}\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "requirements.lock"
            lock_path.write_text(lock_text, encoding="utf-8")
            document = render_spdx(lock_path)
        self.assertEqual(document["spdxVersion"], "SPDX-2.3")
        self.assertEqual(len(document["packages"]), 1)
        package = document["packages"][0]
        self.assertEqual(package["licenseDeclared"], "NOASSERTION")
        self.assertEqual(package["checksums"][0]["checksumValue"], digest)

    def test_pip_report_renders_normalized_hashed_lock(self):
        digest = "a" * 64
        report = {
            "install": [{
                "metadata": {"name": "Demo_Pkg", "version": "1.2.3"},
                "download_info": {
                    "url": "https://example.invalid/demo.whl",
                    "archive_info": {"hashes": {"sha256": digest}},
                },
            }]
        }
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            lock = render_lock(report_path)
        self.assertIn("demo-pkg==1.2.3", lock)
        self.assertIn(f"--hash=sha256:{digest}", lock)

    def test_atms_alternatives_can_coexist(self):
        atms = AtmsProbe()
        atms.assume("m1")
        atms.assume("m2")
        atms.justify(("m1",), "supports_m1")
        atms.justify(("m2",), "supports_m2")
        context = frozenset({"m1", "m2"})
        self.assertTrue(atms.supported_in("supports_m1", context))
        self.assertTrue(atms.supported_in("supports_m2", context))

    def test_atms_nogood_prunes_inconsistent_environment(self):
        atms = AtmsProbe()
        atms.assume("p")
        atms.assume("not_p")
        atms.justify(("p", "not_p"), "contradiction")
        atms.add_nogood(frozenset({"p", "not_p"}))
        self.assertEqual(atms.labels["contradiction"], set())

    def test_atms_labels_keep_only_minimal_environments(self):
        atms = AtmsProbe()
        atms.assume("a")
        atms.assume("b")
        atms.justify(("a",), "q")
        atms.justify(("a", "b"), "q")
        self.assertEqual(atms.labels["q"], {frozenset({"a"})})

    def test_atms_f0_probe_is_explicitly_prototype(self):
        result = run_atms_probe()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["production_engine_selected"])

    def test_pending_component_cannot_be_reported_as_pass(self):
        stages = [{"stage": "source", "status": "PASS"},
                  {"stage": "openmodelica", "status": "PENDING"}]
        self.assertEqual(overall_status(stages), "BLOCKED")

    def test_stub_cannot_be_reported_as_pass(self):
        stages = [{"stage": "candidate", "status": "STUB"}]
        self.assertEqual(overall_status(stages), "BLOCKED")

    def test_failure_takes_precedence_over_pending(self):
        stages = [{"stage": "rdf", "status": "PENDING"},
                  {"stage": "source", "status": "FAIL"}]
        self.assertEqual(overall_status(stages), "FAIL")

    def test_only_all_pass_can_report_pass(self):
        self.assertEqual(overall_status([{"status": "PASS"}, {"status": "PASS"}]), "PASS")

    def test_synthetic_claim_has_an_exact_source_anchor(self):
        stages, annotation = source_and_annotation()
        self.assertEqual(stages[0]["status"], "PASS")
        self.assertTrue(stages[0]["synthetic"])
        self.assertEqual(annotation["target"]["selector"]["exact"],
                         annotation["body"]["value"])
        self.assertTrue(annotation["id"].startswith("https://"))
        self.assertEqual(len(stages), 1)

    def test_semantic_spike_roundtrip_provenance_shacl_and_sparql(self):
        _, annotation = source_and_annotation()
        stages = run_semantic_pipeline(annotation)
        statuses = {stage["stage"]: stage["status"] for stage in stages}
        required = [
            "web_annotation_jsonld_roundtrip",
            "rdf_prov_mapping",
            "shacl_positive_and_negative",
            "sparql_query",
            "crminf_crmsci_mapping",
        ]
        self.assertEqual({name: statuses.get(name) for name in required},
                         {name: "PASS" for name in required})
        mapping = next(stage for stage in stages if stage["stage"] == "crminf_crmsci_mapping")
        self.assertEqual(mapping["crminf_version"], "1.2.1")
        self.assertEqual(mapping["crmsci_version"], "3.2")
        self.assertFalse(mapping["crminf_inference_asserted"])
        self.assertFalse(mapping["crmsci_observation_applicable"])


if __name__ == "__main__":
    unittest.main()
