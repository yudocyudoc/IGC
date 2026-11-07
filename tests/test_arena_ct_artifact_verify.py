"""CT-01 archived bytes, not replay, with adversarial corruption tests."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import unittest

from scripts.arena_cafe.ct_artifact_verify import check_archives


class ArchivedByteTests(unittest.TestCase):
    def test_valid_missing_and_bad_archive_are_not_equivalent(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "github-actions-artifact-11.zip"
            with ZipFile(path, "w") as z:
                z.writestr("result.json", b'{"status":"historical"}')
            base = {"schema": "igc-ct01-authentic-actions-artifact-digests/1.0",
                    "archives": [
                        {"artifact_id": 11, "capability": "D2", "entry_count": 1,
                         "zip_sha256": sha256(path.read_bytes()).hexdigest(),
                         "entries": {"result.json": sha256(b'{"status":"historical"}').hexdigest()}},
                        {"artifact_id": 22, "capability": "R4", "entry_count": 1,
                         "zip_sha256": "a"*64, "entries": {"other.json": "b"*64}},
                    ]}
            output = check_archives(root, base)
            self.assertEqual(output["passed"], 1)
            self.assertEqual(output["missing"], 1)
            self.assertEqual(output["artifacts"][1]["status"], "ARTIFACT_NOT_MOUNTED")
            path.write_bytes(path.read_bytes() + b"changed")
            out = check_archives(root, base)
            self.assertEqual(out["artifacts"][0]["status"], "ZIP_SHA256_MISMATCH")


if __name__ == "__main__":
    unittest.main()
