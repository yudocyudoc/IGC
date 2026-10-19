"""Create a minimal SPDX 2.3 inventory for a hashed requirements lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


def parse_lock(path: Path) -> list[dict]:
    packages = []
    current = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().rstrip(chr(92)).strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("--hash="):
            if current is None:
                raise ValueError("hash appears before a package pin")
            match = re.fullmatch(r"--hash=sha256:([0-9a-f]{64})", line)
            if not match:
                raise ValueError(f"unsupported or malformed hash: {line}")
            current["sha256"] = match.group(1)
            packages.append(current)
            current = None
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\\s]+)\\s*\\\\?", line)
        if not match or current is not None:
            raise ValueError(f"unsupported or malformed lock entry: {line}")
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        current = {"name": name, "version": match.group(2)}
    if current is not None:
        raise ValueError(f"package has no SHA-256 hash: {current['name']}")
    if not packages:
        raise ValueError("lock contains no packages")
    return packages


def render_spdx(lock_path: Path) -> dict:
    packages = parse_lock(lock_path)
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    document_id = str(uuid5(NAMESPACE_URL, lock_sha))
    spdx_packages = []
    relationships = []
    for item in packages:
        package_id = "SPDXRef-Package-" + re.sub(r"[^A-Za-z0-9.-]+", "-", item["name"])
        spdx_packages.append({
            "name": item["name"],
            "SPDXID": package_id,
            "versionInfo": item["version"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "checksums": [{"algorithm": "SHA256", "checksumValue": item["sha256"]}],
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:pypi/{item['name']}@{item['version']}",
            }],
        })
        relationships.append({
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": package_id,
        })
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "IGC F0 Python dependencies",
        "documentNamespace": f"https://example.invalid/igc/sbom/python/{document_id}",
        "creationInfo": {
            "creators": ["Tool: igc-sbom-from-lock/0.1"],
            "created": created,
        },
        "packages": spdx_packages,
        "relationships": relationships,
        "comment": (
            f"Generated from requirements lock SHA-256 {lock_sha}. "
            "License fields are NOASSERTION pending package-by-package review. "
            "This inventory covers Python packages only, not the runner, actions, or containers."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lock", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = render_spdx(args.lock)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(document['packages'])} package records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
