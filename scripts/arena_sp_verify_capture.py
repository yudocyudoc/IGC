"""Audit the complete S/P provider run without making additional AI calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .arena_sp_capture import check_receipt
from .arena_sp_producers import parse_responses, ProviderError
from .arena_round import hash_obj


def verify_archive(package:dict, catalog:dict, directory:Path) -> dict:
    def read(name:str) -> dict:
        file=directory/name
        if not file.is_file():
            raise ProviderError("INCOMPLETE_PROVIDER_ARCHIVE:"+name)
        return json.loads(file.read_text(encoding="utf-8"))
    metadata=read("manifest.json")
    responses=read("provider-responses.json")
    drafts=read("provider-drafts.json")
    receipt=read("provider-receipt.json")
    finished=read("completed.json")
    if metadata.get("state")!="STARTED_NOT_COMPLETED" or metadata.get("run_ref")!=receipt.get("run_ref"):
        raise ProviderError("CAPTURE_START_MISMATCH")
    check_receipt(receipt,package,responses)
    expected=parse_responses(package,responses,catalog)
    if expected!=drafts:
        raise ProviderError("DRAFT_CHANGED_AFTER_PROVIDER_RUN")
    if (finished.get("state")!="COMPLETE_NOT_EMPIRICALLY_EVALUATED"
        or finished.get("receipt_hash")!=receipt["receipt_hash"]
        or finished.get("draft_hash")!=drafts["output_hash"]):
        raise ProviderError("CAPTURE_COMPLETION_MISMATCH")
    for i,row in enumerate(receipt["observations"],1):
        journal=read(f"call-{i}.json")
        if journal.get("observation")!=row or journal.get("response")!=responses[row["model_name"]]:
            raise ProviderError("CALL_JOURNAL_TAMPERED")
    return {"status":"ARCHIVE_CONSISTENT_NOT_INDEPENDENTLY_ATTESTED",
            "calls":3,"run_ref":receipt["run_ref"],
            "receipt_hash":receipt["receipt_hash"],
            "draft_hash":drafts["output_hash"],
            "tokens_status":receipt["tokens_status"],
            "external_attestation":False,
            "empirical_evaluation":False}


def main() -> None:
    p=argparse.ArgumentParser(description="Offline verification of a captured Arena S/P campaign")
    p.add_argument("--package",required=True,type=Path)
    p.add_argument("--catalog",required=True,type=Path)
    p.add_argument("--archive",required=True,type=Path)
    args=p.parse_args()
    read=lambda f:json.loads(f.read_text(encoding="utf-8"))
    result=verify_archive(read(args.package),read(args.catalog),args.archive)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
