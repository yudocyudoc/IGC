"""F0-HIST boundary: active code must not depend on archived CAF-01/02 paths.

This is a static regression, not proof of semantic correctness or scientific inference.
Historical documents and manifests intentionally retain provenance links.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIRS = (
    ROOT / ".github" / "workflows",
    ROOT / "scripts",
    ROOT / "tests",
    ROOT / "experiments",
)
SOURCE_SUFFIXES = {".py", ".mjs", ".js", ".ts", ".sh", ".yml", ".yaml"}


class F0HistoricoBoundaryTests(unittest.TestCase):
    def test_ev_recovery_manifest_matches_copy_and_rewire_claims(self):
        manifest = json.loads(
            (ROOT / "historico" / "manifest_ev_recovery_2026-11-02.json")
            .read_text(encoding="utf-8")
        )
        files = manifest["files"]
        self.assertEqual(8, len(files))
        self.assertEqual(len(files), len({item["promoted"] for item in files}))
        allowed = {"original blob copied", "relocation+minimal import rewiring"}
        for item in files:
            self.assertIn(item["change_type"], allowed)
            target = ROOT / item["promoted"]
            self.assertTrue(target.is_file(), item["promoted"])
            payload = target.read_bytes()
            header = f"blob {len(payload)}".encode("ascii") + bytes([0])
            blob = hashlib.sha1(header + payload).hexdigest()
            source_blob = item["original_blob_sha"]
            with self.subTest(path=item["promoted"], claim=item["change_type"]):
                if item["change_type"] == "original blob copied":
                    self.assertEqual(source_blob, blob)
                else:
                    self.assertNotEqual(source_blob, blob)

    def test_no_active_code_refers_to_retired_cafe_paths(self):
        # Build fragments to keep this test from matching its own fixture text.
        retired_slash = tuple("experiments/cafeteria/pc0" + n for n in ("1", "2"))
        retired_imports = tuple("experiments.cafeteria.pc0" + n for n in ("1", "2"))
        violations = []
        count = 0
        for directory in ACTIVE_DIRS:
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                    continue
                count += 1
                text = path.read_text(encoding="utf-8")
                relative = str(path.relative_to(ROOT))
                for marker in retired_slash:
                    if marker in text:
                        violations.append((relative, "retired-path", marker))
                if path.suffix != ".py":
                    continue
                tree = ast.parse(text, filename=relative)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    for name in names:
                        if name == "historico" or name.startswith("historico."):
                            violations.append((relative, "archive-import", name))
                        if any(name == v or name.startswith(v + ".")
                               for v in retired_imports):
                            violations.append((relative, "retired-import", name))
        self.assertGreater(count, 100, "Active tree unexpectedly empty")
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
