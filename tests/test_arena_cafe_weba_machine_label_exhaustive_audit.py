"""Tests of the WEBA schema-inspection primitive; fixtures are rows, not cafes."""
import hashlib
import unittest

from scripts.arena_cafe import weba_machine_label_exhaustive_audit as audit


class TestMachineLabelExhaustiveAudit(unittest.TestCase):
    def test_plain_numeric_records(self):
        raw = (b"14:18:39.6673,0.2354,-9.8066,0.1177\n"
               b"14:18:39.7100,0.3530,-10.3950,0.0000\n")
        c = audit.scan_file_bytes(raw)
        self.assertEqual(c["valid_time_and_numeric_xyz"], 2)
        self.assertEqual(c["nonblank_rows"], 2)

    def test_non4_field_label_record_is_preserved_not_parsed_as_xyz(self):
        c = audit.scan_file_bytes(
            b"14:18:39.6673,0,1,2,espresso\n")
        self.assertEqual(c["unexpected_column_count"], 1)
        self.assertNotIn("valid_time_and_numeric_xyz", c)

    def test_bad_time_is_not_pretended_machine_cycle(self):
        c = audit.scan_file_bytes(b"coffee,0,1,2\n")
        self.assertEqual(c["unexpected_time_format"], 1)

    def test_invalid_numeric_component_is_separate(self):
        c = audit.scan_file_bytes(b"10:00:00.0000,0,espresso,2\n")
        self.assertEqual(c["nonnumeric_xyz"], 1)

    def test_nan_is_nonfinite(self):
        c = audit.scan_file_bytes(b"10:00:00,0,nan,2\n")
        self.assertEqual(c["nonfinite_xyz"], 1)

    def test_blank_and_crlf_are_counted_separately(self):
        c = audit.scan_file_bytes(b"10:00:00.2,0,1,2\r\n\r\n")
        self.assertEqual(c["valid_time_and_numeric_xyz"], 1)
        self.assertEqual(c["blank_rows"], 1)

    def test_empty_blob_rejected_by_sha_validation(self):
        entry = {
            "path": "B.shift_data/20240104_evening/5.coffee_machine_acc/test",
            "bytes": 3, "git_sha1": "0" * 40, "kind": "STANDARD_FRAGMENT",
            "shift": "20240104_evening",
        }
        with self.assertRaisesRegex(ValueError, "SHA1_DIFFER"):
            audit.scan_entry(entry, fetch=lambda _: b"a,b")

    def test_original_git_blob_hash_verified_locally(self):
        raw = b"10:00:00.00,0,1,2\n"
        sha = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        entry = {
            "path": "B.shift_data/20240104_evening/5.coffee_machine_acc/20240104_100000",
            "bytes": len(raw), "git_sha1": sha, "kind": "STANDARD_FRAGMENT",
            "shift": "20240104_evening",
        }
        result = audit.scan_entry(entry, fetch=lambda _: raw)
        self.assertTrue(result["sha1_verified"])
        self.assertEqual(result["rows"]["valid_time_and_numeric_xyz"], 1)
        self.assertNotIn("raw", str(result))

    def test_partial_tree_never_passes_inventory(self):
        with self.assertRaisesRegex(ValueError, "TREE_TRUNCATED"):
            audit.inventory({"truncated": True, "tree": []})

    def test_unpinned_synthetic_small_manifest_never_pretends_full_scan(self):
        tree = {
            "truncated": False,
            "tree": [
                {"path": "B.shift_data/20240104_evening", "type": "tree"},
                {"path": "B.shift_data/20240104_evening/"
                         "5.coffee_machine_acc/20240104_100000",
                 "type": "blob", "size": 10, "sha": "a" * 40},
            ],
        }
        with self.assertRaisesRegex(ValueError, "SHIFT_COUNT_CHANGED"):
            audit.inventory(tree)


if __name__ == "__main__":
    unittest.main()
