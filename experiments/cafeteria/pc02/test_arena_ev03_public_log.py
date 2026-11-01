"""ARENA EV-03 adversarial XES ingestion quality tests; no real data in tests."""
from __future__ import annotations

import gzip
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import arena_public_eventlog_intake as m
import arena_ev03_public_log_probe as p

SOURCE="https://example.invalid/ev03/test-fixture.xes.gz"


def sample_xml():
    return """<?xml version="1.0" encoding="utf-8"?>
<log xmlns="http://www.xes-standard.org/">
<trace><string key="concept:name" value="PRIVATE_LOAN_001"/>
<event><string key="concept:name" value="SECRET_A_APPLIED"/><date key="time:timestamp" value="2012-01-01T12:00:00+01:00"/><string key="lifecycle:transition" value="COMPLETE"/><string key="org:resource" value="SECRET_EMPLOYEE_1"/></event>
<event><string key="concept:name" value="SECRET_W_WORK"/><date key="time:timestamp" value="2012-01-01T12:30:00+01:00"/><string key="lifecycle:transition" value="START"/></event>
<event><string key="concept:name" value="SECRET_W_WORK"/><date key="time:timestamp" value="2012-01-01T13:00:00+01:00"/><string key="lifecycle:transition" value="COMPLETE"/></event>
</trace>
<trace><string key="concept:name" value="PRIVATE_LOAN_002"/>
<event><string key="concept:name" value="SECRET_B"/><date key="time:timestamp" value="2012-01-02T13:00:00Z"/></event>
<event><string key="concept:name" value="SECRET_B"/><date key="time:timestamp" value="2012-01-02T12:00:00Z"/></event>
</trace></log>"""


def write(root,name,contents):
    path=Path(root)/name
    content=contents.encode("utf-8")
    path.write_bytes(gzip.compress(content,mtime=0) if name.endswith(".gz") else content)
    return path


class ExternalEventLogTests(unittest.TestCase):
    def test_realistic_xes_gzip_aggregate_only_and_source_sha(self):
        with TemporaryDirectory() as tmp:
            f=write(tmp,"fixture.xes.gz",sample_xml())
            r=m.audit_xes_file(f,SOURCE)
            s=r["summary"]
            self.assertEqual(s["n_traces"],2)
            self.assertEqual(s["n_events"],5)
            self.assertEqual(s["events_with_valid_aware_timestamp"],5)
            self.assertEqual(s["events_with_resource_field"],1)
            self.assertEqual(s["cases_with_recorded_timestamp_reverse_order"],1)
            self.assertEqual(s["cases_with_observed_first_last_span"],1)
            self.assertEqual(r["n_distinct_activities"],3)
            self.assertEqual(r["lifecycle_count_by_coarse_tag"],{
                "COMPLETE":2,"START":1})
            self.assertEqual(r["received_file_sha256"],
                             "sha256:"+sha256(f.read_bytes()).hexdigest())
            dump=json.dumps(r)
            for secret in ("PRIVATE_LOAN_001","PRIVATE_LOAN_002",
                           "SECRET_EMPLOYEE_1","SECRET_A_APPLIED",
                           "SECRET_W_WORK","SECRET_B"):
                self.assertNotIn(secret,dump)
            self.assertFalse(r["can_infer_hidden_stages"])
            self.assertFalse(r["can_estimate_cafe_capacity"])

    def test_plain_xes_semantics_and_gzip_same_aggregates(self):
        with TemporaryDirectory() as tmp:
            gz=write(tmp,"fixture.xes.gz",sample_xml())
            raw=write(tmp,"fixture.xes",sample_xml())
            a=m.audit_xes_file(gz,SOURCE)
            b=m.audit_xes_file(raw,SOURCE)
            self.assertEqual(a["summary"],b["summary"])
            self.assertEqual(a["n_distinct_activities"],
                             b["n_distinct_activities"])

    def test_missing_timestamp_timezone_and_activity_are_counted(self):
        x="""<log><trace>
        <event><string key="concept:name" value="PRIVATE_X"/></event>
        <event><date key="time:timestamp" value="2012-01-01T12:00:00"/></event>
        <event><string key="concept:name" value="PRIVATE_X"/>
               <date key="time:timestamp" value="not-time"/></event>
        <event><string key="concept:name" value="PRIVATE_X"/>
               <date key="time:timestamp" value="2012-01-01T12:00:00Z"/></event>
        </trace></log>"""
        with TemporaryDirectory() as tmp:
            r=m.audit_xes_file(write(tmp,"missing.xes",x),SOURCE)
            s=r["summary"]
            self.assertEqual(s["n_events"],4)
            self.assertEqual(s["events_missing_timestamp"],1)
            self.assertEqual(s["events_without_timezone"],1)
            self.assertEqual(s["events_bad_timestamp"],1)
            self.assertEqual(s["events_with_valid_aware_timestamp"],1)
            self.assertEqual(s["events_missing_activity"],1)
            self.assertEqual(s["cases_with_observed_first_last_span"],0)

    def test_dtd_and_entities_rejected_even_later_in_source(self):
        bad='''<?xml version="1.0"?>
        <!DOCTYPE log [<!ENTITY exploit SYSTEM "file:///etc/passwd">]>
        <log><trace><event><string key="concept:name" value="&exploit;"/>
        </event></trace></log>'''
        with TemporaryDirectory() as tmp:
            f=write(tmp,"attack.xes.gz",bad)
            with self.assertRaises(Exception):
                m.audit_xes_file(f,SOURCE)

    def test_limits_and_invalid_extensions_rejected(self):
        with TemporaryDirectory() as tmp:
            f=write(tmp,"fixture.xes.gz",sample_xml())
            with self.assertRaisesRegex(ValueError,"EV03_COMPRESSED_BYTE_LIMIT"):
                m.audit_xes_file(f,SOURCE,compressed_limit=10)
            with self.assertRaisesRegex(ValueError,"EV03_DECOMPRESSED_BYTE_LIMIT"):
                m.audit_xes_file(f,SOURCE,plain_limit=50)
            no=write(tmp,"unknown.csv",sample_xml())
            with self.assertRaisesRegex(ValueError,"EV03_UNSUPPORTED_SOURCE_EXTENSION"):
                m.audit_xes_file(no,SOURCE)
            with self.assertRaisesRegex(ValueError,"EV03_SOURCE_PROVENANCE_REQUIRED"):
                m.audit_xes_file(f,"file:///private")

    def test_empty_log_does_not_count_as_external_evidence(self):
        with TemporaryDirectory() as tmp:
            f=write(tmp,"empty.xes","<log></log>")
            with self.assertRaisesRegex(ValueError,"EV03_EMPTY_LOG"):
                m.audit_xes_file(f,SOURCE)

    def test_clocks_utc_offset_and_no_timezone(self):
        self.assertEqual(
            m.parse_aware("2012-01-01T12:00:00+01:00"),
            m.parse_aware("2012-01-01T11:00:00Z"))
        with self.assertRaisesRegex(ValueError,"EV03_TIMESTAMP_NO_OFFSET"):
            m.parse_aware("2012-01-01T12:00:00")
        with self.assertRaisesRegex(ValueError,"EV03_TIMESTAMP_MALFORMED"):
            m.parse_aware("unknown")

    def test_real_business_readiness_requires_source_documents(self):
        empty=m.readiness_gate({})
        self.assertFalse(empty["all_fields_supplied"])
        self.assertFalse(empty["physical_service_inference_authorized"])
        filled={k:"This is a synthetic unsigned document reference"
                for k in m.REQUIRED_SOURCE_DOCUMENTATION}
        some=m.readiness_gate(filled)
        self.assertTrue(some["all_fields_supplied"])
        self.assertFalse(some["clock_independently_validated"])
        self.assertFalse(some["data_use_authorization_independently_verified"])

    def test_orchestrator_writes_manifest_without_any_raw_identity(self):
        with TemporaryDirectory() as tmp:
            inp=write(tmp,"fixture.xes.gz",sample_xml())
            root=Path(tmp)/"audit"
            r=p.run(root,inp,SOURCE,"SYNTHETIC_XES_FIXTURE","a"*40,"b"*40)
            self.assertEqual(r["external_audit"]["status"],
                             "SYNTHETIC_PARSER_TEST_ONLY")
            self.assertTrue(r["no_unauthorized_business_records_used"])
            plan=json.loads((root/"00_PLAN_BEFORE_PARSE.json").read_text())
            self.assertEqual(plan["first_protocol_commit"],p.PROTO)
            self.assertTrue(plan["no_republication_of_source_rows"])
            manifest=json.loads((root/"03_MANIFEST.json").read_text())
            for name,digest in manifest["files_sha256"].items():
                self.assertEqual(digest,"sha256:"+
                    sha256((root/name).read_bytes()).hexdigest())
            for f in root.iterdir():
                source=f.read_text()
                self.assertNotIn("PRIVATE_LOAN",source)
                self.assertNotIn("SECRET_EMPLOYEE",source)
            with self.assertRaisesRegex(ValueError,"EV03_REFUSE_OVERWRITE"):
                p.run(root,inp,SOURCE,"SYNTHETIC_XES_FIXTURE","a"*40,"b"*40)

    def test_public_source_only_pinned_4tu_not_fake_real(self):
        with TemporaryDirectory() as tmp:
            inp=write(tmp,"fixture.xes.gz",sample_xml())
            with self.assertRaisesRegex(ValueError,"EV03_WRONG_PUBLIC_SOURCE"):
                p.run(Path(tmp)/"other",inp,SOURCE,"PUBLIC_REAL_BPI12",
                      "a"*40,"b"*40)


if __name__=="__main__":
    unittest.main(verbosity=2)
