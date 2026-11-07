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
        # Test real physical-job shell and dependency commands; not a
        # hand-selected list of regex tokens or a synthetic reduced workflow.
        workflow.write_text((Path(__file__).resolve().parents[1] / WORKFLOW).read_text())
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


    def test_start_time_and_original_library_origin_are_numeric(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            base=self.make_repo(root)
            wf=root/WORKFLOW
            self.assertIn("startTime=0",wf.read_text())
            wf.write_text(wf.read_text().replace("startTime=0","startTime=1"))
            cmd(root,"add",".");cmd(root,"commit","-qm","changed physical start time")
            result=decision(root,base)
            self.assertTrue(result["numerical_changed"])
            self.assertEqual(result["status"],"BLOCKED_NUMERICAL_DRIFT_REQUIRES_EXPLICIT_BUDGET")
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            base=self.make_repo(root)
            wf=root/WORKFLOW
            self.assertIn("modelica-3rdparty/SystemDynamics.git",wf.read_text())
            wf.write_text(wf.read_text().replace(
                "modelica-3rdparty/SystemDynamics.git",
                "different-org/SystemDynamics.git"))
            cmd(root,"add",".");cmd(root,"commit","-qm","changed numerical library origin")
            result=decision(root,base)
            self.assertTrue(result["numerical_changed"])
            self.assertEqual(result["status"],"BLOCKED_NUMERICAL_DRIFT_REQUIRES_EXPLICIT_BUDGET")

    def test_non_numeric_workflow_metadata_does_not_force_omc(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            base=self.make_repo(root)
            wf=root/WORKFLOW
            wf.write_text(wf.read_text().replace(
                "Recover original three M3 candidates, two worlds, and six parameter-shift worlds",
                "Human-readable step title changed").replace(
                "retention-days: 60","retention-days: 30"))
            cmd(root,"add",".");cmd(root,"commit","-qm","metadata only")
            self.assertFalse(decision(root,base)["numerical_changed"])


if __name__ == "__main__":
    unittest.main()
