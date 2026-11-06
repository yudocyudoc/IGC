"""E04 action semantics and isolation between producer/evaluator artifact mounts."""
import json
import os
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe import e04_action_capability as a
from scripts.arena_cafe.native_handoff import need

class E04ActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d=os.environ.get('E04_D_DIR'); m=os.environ.get('E04_M_DIR')
        if not d or not m:
            raise unittest.SkipTest('Need both frozen E03 D/M producer artifacts')
        cls.dm=json.loads((Path(d)/'manifest.json').read_text())
        cls.mm=json.loads((Path(m)/'manifest.json').read_text())
        cls.ds=json.loads((Path(d)/'scores.json').read_text())
        cls.ms=json.loads((Path(m)/'scores.json').read_text())

    def test_cannot_translate_generic_stock_name_to_dispatch(self):
        r=a.producer(self.dm,self.mm,self.ds,self.ms)
        self.assertEqual(r['status'],'E04_PARTIAL_D_M_REPRESENTATION_GAP_B_NOT_EXECUTED')
        self.assertEqual((r['arms']['D']['mapped'],r['arms']['M']['mapped']),(0,0))
        self.assertEqual((r['arms']['D']['attempted'],r['arms']['M']['attempted']),(81,54))
        self.assertEqual(r['E05_gate'],'BLOCKED_NO_ADMISSIBLE_LOCAL_ACTION_PREDICTION')
        self.assertTrue(all(x['status']=='INTERVENTION_NOT_REPRESENTABLE' and
                            x['predicted_action_effect'] is None for arm in ('D','M')
                            for x in r['arms'][arm]['candidates']))
        self.assertEqual(r['B']['status'],'NATIVE_NOT_EXECUTED')
        self.assertFalse(r['B']['abstention'])

    def test_fake_m_dispatch_semantics_rejected(self):
        tampered=deepcopy(self.mm)
        node=next(x for x in tampered['candidates'][0]['variant_ast']['instances']
                  if x['role']=='dispatch')
        node['class_id']='fictional-fcfs-server'
        with self.assertRaises(ValueError):
            a.producer(self.dm,tampered,self.ds,self.ms)

    def test_cross_source_submission_rejected(self):
        tampered=deepcopy(self.ms)
        tampered['source_snapshot_hash']='sha256:other-world'
        with self.assertRaises(ValueError):
            a.producer(self.dm,self.mm,self.ds,tampered)

    def test_no_f4_evaluator_mount_on_producer(self):
        root=os.environ.get('E04_F4_MOUNT')
        if root:
            self.assertFalse(Path(root).exists())

if __name__=='__main__':unittest.main()