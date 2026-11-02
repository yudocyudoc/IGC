"""Minimal non-overwriting artefact writer promoted from CAF-07B dependencies.

Behavior matches caf02_public_cut_bridge.canonical / caf02_lab_exploratorio.write_new
at main@5e2b550. This module does not import the historical hypothesis bank.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re

SOURCE_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def write_new(folder, name, data):
    target = Path(folder) / name
    raw = ((json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()
           if isinstance(data, (dict, list)) else data.encode("utf-8"))
    with target.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return "sha256:" + sha256(raw).hexdigest()
