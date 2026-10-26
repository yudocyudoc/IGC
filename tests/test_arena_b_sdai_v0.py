"""B0 tests: Buffalo scalar process adapted without generating mechanisms."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arena_v0_contract import ArenaContractError, digest
from scripts.arena_b_sdai_v0 import (
    BuffaloBridgeError, PROMPT_PATH, SOURCE_COMMIT,
    accept, encode_expression, make_request, render_model, validate_model
)

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT/"data/synthetic/arena_b_v0_handwritten_sdjson.json").read_text())


def visible():
    return json.loads((ROOT/"data/synthetic/arena_b_v0_visible.json").read_text())


class BuffaloIndependentB0Tests(unittest.TestCase):
    def test_true_buffalo_process_prompt_pinned_and_not_d_method(self):
        request=make_request(visible())
        self.assertEqual(request["arm_id"],"B")
        self.assertEqual(request["upstream_commit"],SOURCE_COMMIT)
        self.assertEqual(request["provider_status"],"NOT_CALLED_PREPARATION_ONLY")
        self.assertEqual(request["input_hash"],digest(visible()))
        self.assertIn("MANDATORY PROCESS",request["prompt"]["system"])
        self.assertIn("STOCK",request["prompt"]["system"])
        self.assertIn("FLOW",request["prompt"]["system"])
        self.assertNotIn("Molecule",request["prompt"]["system"])
        self.assertEqual(request["currentModel"],{"variables":[],"relationships":[]})
        self.assertEqual(request["supportsArrays"],False)
        self.assertEqual(request["supportsModules"],False)
        self.assertEqual(request["supportsSubTypes"],False)
        self.assertEqual(request["prompt"]["system"],PROMPT_PATH.read_text())
        self.assertNotIn("CS-01",str(request))

    def test_exact_sd_json_structure_valid(self):
        record=fixture()
        native=record["model"]
        parsed=validate_model(native)
        self.assertEqual(len(parsed["stocks"]),2)
        self.assertEqual(len(parsed["flows"]),2)
        model,code=render_model(native)
        self.assertTrue(model.startswith("BuffaloSFD_"))
        self.assertIn("der(Pending_Work) = (Arrival_Flow) - (Completion_Flow);",code)
        self.assertIn("der(Completed_Work) = (Completion_Flow) - (0);",code)
        self.assertIn("Completion_Flow = max(0, min(Service_Capacity, (Pending_Work / Service_Time)));",code)
        self.assertNotIn("IGCMolecules",code)
        self.assertNotIn("DStockFlow",code)

    def test_no_modelica_if_unknown_formula(self):
        base=fixture()["model"]
        v=next(x for x in base["variables"] if x["name"]=="Completion Flow")
        for equation in ("not_a_declared_symbol", "eval(1+2)",
                         "__import__('os').system('id')","Pending_Work[0]",
                         "5 if TIME > 1 else 1","NaN"):
            n=copy.deepcopy(base)
            next(x for x in n["variables"] if x["name"]=="Completion Flow")["equation"]=equation
            with self.subTest(equation=equation),self.assertRaises(BuffaloBridgeError):
                render_model(n)

    def test_no_silent_molecular_or_stock_completion(self):
        record=fixture()["model"]
        for mutate in (
            lambda n: n["variables"].pop(0),
            lambda n: n["variables"][0].update(outflows=["Unknown Flow"]),
            lambda n: n["variables"][0].update(inflows=["Completion Flow"],
                                               outflows=["Completion Flow"]),
            lambda n: n["variables"][0].update(subType="queue"),
            lambda n: n.update(modules=[]),
            lambda n: n["variables"][0].update(inflows=["Arrival Flow","Arrival Flow"]),
            lambda n: n["variables"][0].update(units="people"),
        ):
            n=copy.deepcopy(record)
            mutate(n)
            with self.subTest(mutate=str(mutate)),self.assertRaises(BuffaloBridgeError):
                render_model(n)

    def test_reject_multiple_consumers_of_same_material(self):
        native=fixture()["model"]
        extra=copy.deepcopy(native["variables"][1])
        extra["name"]="Extra Completed Work"
        native["variables"].append(extra)
        with self.assertRaisesRegex(BuffaloBridgeError,"DUPLICATED_MATERIAL_FLOW"):
            validate_model(native)

    def test_explicit_nonexecutability_if_b_only_cld(self):
        cld={"variables":[{"name":"waiting","type":"variable","equation":"1"}],
             "relationships":[]}
        with self.assertRaisesRegex(BuffaloBridgeError,"STOCK_OR_FLOW_REQUIRED"):
            render_model(cld)

    def test_no_forbidden_evaluator_or_other_arm_input(self):
        d=visible()
        d["construction"]["gold"]="secret"
        with self.assertRaises(ArenaContractError):
            make_request(d)
        for name in ("other_arm_result","holdout","reserved_observations"):
            d=visible()
            d["construction"][name]="secret"
            with self.subTest(name=name),self.assertRaises(ArenaContractError):
                make_request(d)

    def test_fails_closed_for_invalid_response_provenance(self):
        for origin in ("FAKE_LIVE","UNVERIFIED","D"):
            payload=fixture()
            payload["origin"]=origin
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(BuffaloBridgeError,"INVALID_RESPONSE_PROVENANCE"):
                    accept(visible(),payload,Path(tmp)/"candidate")

    def test_trace_and_submissions_preserve_upstream_sd_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/"bundle"
            record=fixture()
            result=accept(visible(),record,folder)
            native=json.loads((folder/"sd-ai-native.json").read_text())
            sub=json.loads((folder/"submission.json").read_text())
            event=json.loads((folder/"memory-event.json").read_text())
            self.assertEqual(native,record)
            self.assertEqual(sub["arm_id"],"B")
            self.assertEqual(sub["native_artifact_sha256"],digest(record))
            self.assertEqual(event["payload_hash"],digest(record))
            self.assertEqual(event["arm_id"],"B")
            self.assertEqual(result["source_origin"],"HANDWRITTEN_SYNTHETIC_FIXTURE")
            self.assertEqual(len(list(folder.glob("BuffaloSFD_*.mo"))),1)
            with self.assertRaisesRegex(BuffaloBridgeError,"OUTPUT_ALREADY_EXISTS"):
                accept(visible(),record,folder)

    def test_cannot_fake_provider_by_changing_fixture_origin(self):
        record=fixture()
        # Origin is a declared source annotation, NOT cryptographic attestation;
        # G1 checks cannot prove that a model truly came from Buffalo or any LLM.
        record["origin"]="UPSTREAM_PROVIDER_OUTPUT"
        with tempfile.TemporaryDirectory() as tmp:
            result=accept(visible(),record,Path(tmp)/"out")
            self.assertEqual(result["source_origin"],"UPSTREAM_PROVIDER_OUTPUT")
            self.assertIn("NO_PROVIDER_ASSERTION",result["proof_limit"])


if __name__=="__main__":
    unittest.main()
