"""Protect original D/B/M *sources*, without faking a paid Buffalo call.

Git blob identity is not a scientific performance claim; changing a native
engine requires an explicitly reviewed provenance update.
"""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "scripts/arena_d_v01.py": "9dcab2bf1ee3a3c7430595385f381d89ba023a6d",
    "scripts/arena_d_v1_screen.py": "700ed6d10b3d094104ee5c74d1459736e1220f41",
    "scripts/arena_d_v2_revision.py": "ab3f98e87f49746371e7807a9d8e65bcc5089374",
    "scripts/arena_b_native_runner.mjs": "572656687ae2e6b6fce0031b7eb02dbab5868990",
    "scripts/arena_b_openrouter_cloudflare.mjs": "0a93a48d42e6b04c87e8dda3cf18e643785dfbc8",
    "scripts/arena_b_cf_protocol_adapter.mjs": "724843043e699efbfc20fa79be3c0edb08a95c98",
    "scripts/arena_m_short_e1.py": "d7a3345f8ee0169445369e573658a1e004fd8146",
    "scripts/arena_m3_common.py": "5173bf061eec5684e99bbce40d403de51fd0767b",
    "experiments/e1/composer.py": "27d9fe2e65db924f204423f9660a576e723bfd9b",
    "experiments/e1/backend.py": "cc854a0f29399a8299146271fbe3c56c7c5347b3",
    "experiments/e1/registry.base.json": "956eb9636046165b827275a822f37f3643dc1e59",
    "experiments/e1/registry.extended.json": "63a038ff3c6d88477f2ac3e2fb1a08efd29b15ac",
    "experiments/e0/catalog.json": "8381e7aa7280d71aefffdfb26866e007c7678d32",
    "src/modelica/IGCMolecules.mo": "2f83de72d38d0b8f5e866295b806d19067c5194d",
    "src/modelica/IGCInformationMolecules.mo": "36d97a7e9de4d7ee80bf884beec6094a9bb1cf98",
}


class NativeEnginesOriginalTests(unittest.TestCase):
    def test_native_sources_exact_original_blobs(self):
        for path, sha in SOURCES.items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                git_blob = hashlib.sha1(
                    f"blob {len(raw)}".encode() + bytes([0]) + raw
                ).hexdigest()
                self.assertEqual(git_blob, sha)

    def test_d_generates_genuine_six_alternatives(self):
        import json
        from scripts.arena_d_v01 import generate
        data = json.loads((ROOT / "data/synthetic/arena_d_v01_visible.json").read_text())
        native = generate(data)
        self.assertEqual(len(native["candidates"]), 6)
        structures = {c["structure_hash"] for c in native["candidates"]}
        self.assertEqual(len(structures), 6)
        self.assertEqual(native["arm_id"], "D")
        self.assertTrue(all(c["parameter_status"] == "PUBLIC_ASSUMPTIONS_NOT_FITTED"
                            for c in native["candidates"]))

    def test_m_original_composer_enumerates_base_and_extended(self):
        from scripts.arena_m_short_e1 import E1, get_composer
        c = get_composer()
        counts = []
        for name in ("registry.base.json", "registry.extended.json"):
            cfg, classes, catalog = c.load_registry(E1 / name)
            counts.append(len(c.enumerate_graphs(cfg, classes)))
        self.assertEqual(counts, [6, 15])

    def test_b_original_upstream_path_is_not_mock_equivalent(self):
        runner = (ROOT / "scripts/arena_b_native_runner.mjs").read_text()
        self.assertIn('UB-IAD/sd-ai', runner)
        self.assertIn('5199f7b45f3a7ae4a773cb0dd8542940aabe9edc', runner)
        self.assertIn('engines/quantitative/engine.js', runner)
        self.assertIn('utilities/LLMWrapper.js', runner)
        self.assertIn('BUFFALO_MODE ?? "mock"', runner)
        self.assertIn('BUFFALO_LIVE_AUTH', runner)
        # Static protection only: no live call, no native model claimed.
        self.assertNotIn("ORIGINAL_ENGINE_LIVE_OUTPUT_RETURNED\";\\nconst mode", runner)


if __name__ == "__main__":
    unittest.main()
