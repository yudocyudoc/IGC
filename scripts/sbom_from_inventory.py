"""Generate an SPDX 2.3 snapshot for the F0 CI platform."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


from scripts.sbom_from_lock import parse_lock


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "-", value).strip("-") or "item"


def read_dpkg_inventory(path: Path, scope: str) -> list[dict]:
    packages = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3 or any(not field for field in fields):
            raise ValueError(f"{path}:{number}: expected package, version, architecture")
        name, version, architecture = fields
        packages.append({
            "name": name,
            "version": version,
            "architecture": architecture,
            "scope": scope,
        })
    if not packages:
        raise ValueError(f"{path}: empty package inventory")
    return packages


def read_pinned_actions(workflow_path: Path) -> list[dict]:
    pattern = re.compile(r"^[ \t]*uses:[ \t]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})[ \t]+#[ \t]*(v[0-9][A-Za-z0-9_.-]*)[ \t]*$")
    actions = []
    for number, line in enumerate(workflow_path.read_text(encoding="utf-8").splitlines(), 1):
        match = pattern.fullmatch(line)
        if match:
            actions.append({"name": match.group(1), "commit": match.group(2), "version": match.group(3)})
        elif re.search(r"^[ \t]*uses:[ \t]+[^#]+", line):
            raise ValueError(f"{workflow_path}:{number}: action is not pinned by a full commit SHA with version comment")
    if not actions:
        raise ValueError(f"{workflow_path}: no pinned actions found")
    return actions


def _package(record: dict, index: int) -> dict:
    name = record["name"]
    version = record.get("version", "NOASSERTION")
    package_id = f"SPDXRef-{_slug(record['scope'])}-{_slug(name)}-{index}"
    item = {
        "name": name,
        "SPDXID": package_id,
        "versionInfo": version,
        "downloadLocation": record.get("downloadLocation", "NOASSERTION"),
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
        "primaryPackagePurpose": record.get("purpose", "APPLICATION"),
        "comment": record.get("comment", f"Inventory scope: {record['scope']}."),
    }
    if "checksums" in record:
        item["checksums"] = record["checksums"]
    if record.get("purl"):
        item["externalRefs"] = [{
            "referenceCategory": "PACKAGE-MANAGER",
            "referenceType": "purl",
            "referenceLocator": record["purl"],
        }]
    return item


def render_platform_spdx(lock_path: Path, runner_path: Path, container_path: Path,
                         workflow_path: Path, runner_label: str, image_ref: str,
                         image_digest: str) -> dict:
    packages = []
    for item in parse_lock(lock_path):
        packages.append({
            "name": item["name"],
            "version": item["version"],
            "scope": "python-lock",
            "purl": f"pkg:pypi/{item['name']}@{item['version']}",
            "checksums": [{"algorithm": "SHA256", "checksumValue": item["sha256"]}],
            "comment": "Installed in the isolated Python environment from requirements-f0.lock.txt.",
        })
    packages.extend(read_dpkg_inventory(runner_path, "github-runner-dpkg"))
    packages.extend(read_dpkg_inventory(container_path, "openmodelica-image-dpkg"))
    for action in read_pinned_actions(workflow_path):
        packages.append({
            "name": action["name"],
            "version": action["version"] + "+" + action["commit"],
            "scope": "github-action",
            "downloadLocation": f"https://github.com/{action['name']}/tree/{action['commit']}",
            "purl": f"pkg:github/{action['name']}@{action['commit']}",
            "comment": "Action source pinned by full commit SHA in the workflow.",
        })
    packages.extend([
        {
            "name": "GitHub-hosted runner image",
            "version": runner_label,
            "scope": "github-runner-image",
            "purpose": "OPERATING-SYSTEM",
            "downloadLocation": "NOASSERTION",
            "comment": "GitHub-hosted image label is managed by GitHub and is mutable; dpkg package snapshot is attached separately.",
        },
        {
            "name": image_ref,
            "version": image_digest,
            "scope": "openmodelica-container-image",
            "purpose": "CONTAINER",
            "downloadLocation": f"docker://{image_ref}",
            "checksums": [{"algorithm": "SHA256", "checksumValue": image_digest.removeprefix("sha256:")}],
            "comment": "Container image referenced by digest in the F0 workflow.",
        },
    ])
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    content_hash = hashlib.sha256(
        lock_path.read_bytes() + runner_path.read_bytes() + container_path.read_bytes()
        + workflow_path.read_bytes() + image_digest.encode()
    ).hexdigest()
    document_namespace = f"https://example.invalid/igc/sbom/platform/{content_hash}"
    spdx_packages = [_package(item, index) for index, item in enumerate(packages, 1)]
    relationships = [{
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": item["SPDXID"],
    } for item in spdx_packages]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "IGC F0 GitHub Actions platform snapshot",
        "documentNamespace": document_namespace,
        "creationInfo": {
            "creators": ["Tool: igc-platform-sbom/0.1"],
            "created": created,
        },
        "packages": spdx_packages,
        "relationships": relationships,
        "comment": (
            f"Snapshot content hash: {content_hash}. Covers {len(parse_lock(lock_path))} Python lock packages, "
            f"{len(read_dpkg_inventory(runner_path, 'github-runner-dpkg'))} runner dpkg packages, "
            f"{len(read_dpkg_inventory(container_path, 'openmodelica-image-dpkg'))} OpenModelica image dpkg packages, "
            f"{len(read_pinned_actions(workflow_path))} pinned GitHub Actions, runner image label, and OpenModelica image digest. "
            "All license and copyright fields are NOASSERTION pending the separately scheduled license review. "
            "The GitHub runner label is mutable; this is an inventory snapshot, not a claim that the runner image is immutable."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--runner-packages", type=Path, required=True)
    parser.add_argument("--container-packages", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--runner-label", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.image_digest):
        parser.error("--image-digest must be sha256:<64 lowercase hex characters>")
    document = render_platform_spdx(
        args.lock, args.runner_packages, args.container_packages, args.workflow,
        args.runner_label, args.image_ref, args.image_digest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(document['packages'])} SPDX package records to {args.output}")
    print(document["comment"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
