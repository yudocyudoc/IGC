"""CT-00 numerical gate regression tests; no external solver or network."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest

from scripts.arena_ct_numeric_gate import EXACT, WORKFLOW, decision


def cmd(path, *args):
    return subprocess.check_output(["git", *args], cwd=path, stderr=subprocess.PIPE).decode().strip()


class NumericGateTest(unittest.TestCase):
    def make_repo(self, root):
        root = Path(root)
        cmd(root, "init", "-q")
        cmd(root, "config", "user.name", "CT Test")
        cmd(root, "config", "user.email", "ct@example.invalid")
        for name in EXACT:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source-v1\n")
        model = root / "src/modelica/IGCMolecules.mo"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("model Test end Test;\n")
        workflow = root / WORKFLOW
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(
            'docker pull openmodelica/openmodelica:v1.26.5-minimal\n'
            'git clone --branch v4.0.0 msl\n'
            'git clone --branch v2.1.2 sd\n'
            'simulate(Case,stopTime=4,numberOfIntervals=80,method="dassl",tolerance=1e-8)\n'
        )
        cmd(root, "add", ".")
        cmd(root, "commit", "-qm", "baseline")
        return cmd(root, "rev-parse", "HEAD")

    def test_doc_and_memory_tests_do_not_reexecute_physics(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self.make_repo(root)
            (root / "docs").mkdir()
            (root / "docs/note.md").write_text("an added note")
            cmd(root, "add", ".")
            cmd(root, "commit", "-qm", "docs only")
            result = decision(root, baseline)
            self.assertEqual(result["status"], "REUSE_HISTORICAL_NUMERIC_IDENTITY_NO_OMC")
            self.assertEqual(result["planned_simulations"], 0)

    def test_numeric_change_blocks_unbudgeted_and_can_be_authorized(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self.make_repo(root)
            (root / "scripts/arena_m3_prepare.py").write_text("changed equations\n")
            cmd(root, "add", ".")
            cmd(root, "commit", "-qm", "numeric change")
            rejected = decision(root, baseline)
            self.assertTrue(rejected["numerical_changed"])
            self.assertEqual(rejected["status"], "BLOCKED_NUMERICAL_DRIFT_REQUIRES_EXPLICIT_BUDGET")
            self.assertFalse(decision(root, baseline, requested=True, budget=13)["physical_authorized"])
            approved = decision(root, baseline, requested=True, budget=14)
            self.assertTrue(approved["physical_authorized"])
            self.assertEqual(approved["planned_simulations"], 14)

    def test_solver_change_is_numeric_change(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = self.make_repo(root)
            wf = root / WORKFLOW
            wf.write_text(wf.read_text().replace("method=\"dassl\"", "method=\"euler\""))
            cmd(root, "add", ".")
            cmd(root, "commit", "-qm", "solver changed")
            self.assertTrue(decision(root, baseline)["numerical_changed"])


if __name__ == "__main__":
    unittest.main()
