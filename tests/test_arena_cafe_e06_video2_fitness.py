"""E06 independent offline regressions. Real ZIP is mounted only in local source audit.

CI without that private source tests the verifier and boundary rules, but does
NOT claim to re-run the original source audit or re-verify video bytes.
"""
import csv
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.arena_cafe import e06_video2_fitness as e06


def span(a,b):
    return {"observado_desde_video_s":str(a),"observado_hasta_video_s":str(b)}


class E06BoundaryTests(unittest.TestCase):
    def test_01_two_fixed_windows_and_true_crossing_not_split(self):
        a,b=e06.WINDOWS
        self.assertEqual((a,b),((Decimal(0),Decimal(300)),(Decimal(300),Decimal(600))))
        cross=span('299.8','300.2')
        self.assertTrue(e06._interval_overlap(cross,*a))
        self.assertTrue(e06._interval_overlap(cross,*b))
        self.assertFalse(e06._interval_overlap(span(300,300),*a))
        self.assertTrue(e06._interval_overlap(span(300,300),*b))
        self.assertFalse(e06._interval_overlap(span(600,600),*b))
        self.assertTrue(e06._interval_overlap(span(0,0),*a))

    def test_02_nonfinite_or_reversed_time_refused(self):
        for t in ('NaN','Infinity','-Infinity','not-a-time',''):
            with self.subTest(t=t),self.assertRaises(ValueError):
                e06._interval_overlap(span(t,'300'),*e06.WINDOWS[0])
        with self.assertRaisesRegex(ValueError,'SPAN_REVERSED'):
            e06._interval_overlap(span('300.1','299.1'),*e06.WINDOWS[0])

    def test_03_duplicate_zip_filename_refused_even_if_inventory_exists(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'duplicate.zip'
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(p,'w') as z:
                    z.writestr('VIDEO2_SOURCE_INVENTORY.json','{}')
                    z.writestr('VIDEO2_SOURCE_INVENTORY.json','{}')
            with self.assertRaisesRegex(ValueError,'DUPLICATE_ZIP_MEMBER'):
                e06.verified_members(p,expected_sha=hashlib.sha256(p.read_bytes()).hexdigest())

    def test_04_path_traversal_refused_before_inventory_parse(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'traversal.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('VIDEO2_SOURCE_INVENTORY.json','{}')
                z.writestr('../secrets.txt','do not extract')
            with self.assertRaisesRegex(ValueError,'UNSAFE_ZIP_MEMBER'):
                e06.verified_members(p,expected_sha=hashlib.sha256(p.read_bytes()).hexdigest())

    def test_05_archive_substitution_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'other.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('VIDEO2_SOURCE_INVENTORY.json','{}')
            with self.assertRaisesRegex(ValueError,'ZIP_SHA256_MISMATCH'):
                e06.verified_members(p)

    def test_06_unchanged_source_required_and_no_fake_clock(self):
        self.assertEqual(e06.ZIP_SHA256,
                         'eb1c619de072a5790182cd7eb060f9d8b0c6a163acdfd6c18e0af3986fec23e8')
        self.assertEqual(e06.V2_SHA256,
                         '1e81b5464d871cb621e18dd8880a99ccb33be714e458785e25cb345099336d72')
        self.assertEqual(e06.METRICS,'video2/lote_L001_v2/metricas.csv')


@unittest.skipUnless(os.getenv('E06_VIDEO2_SOURCE_ZIP'),
                     'Original investigator ZIP not mounted in this execution; no false real-source CI claim')
class E06OriginalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=Path(os.environ['E06_VIDEO2_SOURCE_ZIP'])
        cls.members,cls.inventory_hash=e06.verified_members(cls.p)

    def test_07_real_two_window_source_and_negative_fitness(self):
        r=e06.audit_members(self.members,self.inventory_hash)
        self.assertEqual(r['status'],'SOURCE_NOT_FIT_FOR_THIS_QUESTION')
        self.assertEqual([w['master_records_with_evidence_span_intersecting_window']
                          for w in r['windows']],[124,72])
        self.assertEqual(r['evidence_spans_crossing_fixed_cuts']['300'],2)
        self.assertEqual(r['l001_evidence']['confirmed_receptions_in_first_window'],2)
        self.assertEqual(r['unit_boundary']['complete_input_output_pairs'],0)
        self.assertFalse(r['source']['physical_clock_verified'])
        self.assertEqual(r['version_reconciliation']['v2_added_derived_interval_rows'],7)
        self.assertEqual(r['E07'],'NOT_TRIGGERED_NO_NEW_OBSERVED_INCREMENTAL_PROCESS_REGULARITY')

    def test_08_false_physical_clock_claim_refused(self):
        data=dict(self.members)
        rows=e06._csv(data[e06.MASTER_V2])
        rows[0]['velocidad_real_verificada']='true'
        out=io.StringIO()
        w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
        data[e06.MASTER_V2]=out.getvalue().encode('utf-8')
        with self.assertRaisesRegex(ValueError,'SOURCE_CLOCK_OR_SERVICE_ATTESTATION_CHANGED'):
            e06.audit_members(data,self.inventory_hash)

    def test_09_unjustified_individual_identity_refused(self):
        data=dict(self.members)
        rows=e06._csv(data[e06.MASTER_V2])
        rows[0]['recipiente_id']='fictitious_cup'
        out=io.StringIO()
        w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
        data[e06.MASTER_V2]=out.getvalue().encode('utf-8')
        with self.assertRaises(ValueError):
            e06.audit_members(data,self.inventory_hash)

    def test_10_modified_historical_v2_lineage_refused(self):
        data=dict(self.members)
        rows=e06._csv(data[e06.MASTER_V2]);rows[0]['notas']+=' fabricated'
        out=io.StringIO()
        w=csv.DictWriter(out,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
        data[e06.MASTER_V2]=out.getvalue().encode('utf-8')
        with self.assertRaisesRegex(ValueError,'UNDECLARED_V1_V2_REVISION'):
            e06.audit_members(data,self.inventory_hash)


if __name__=='__main__':unittest.main()