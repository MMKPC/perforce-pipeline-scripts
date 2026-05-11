"""
p4_pipeline/submit_hook.py
Perforce pre-submit validation hook.
Blocks submits that contain assets violating naming/extension rules.
"""

from __future__ import annotations
import re
from typing import Any

try:
    import P4
except ImportError:
    raise ImportError("Install P4Python: pip install p4python")

BLOCKED_EXTENSIONS = {".tmp", ".bak", ".log", ".DS_Store"}
NAMING_PATTERN     = re.compile(r"^[A-Z][A-Za-z0-9_/\.]+$")


def run_pre_submit_check(port: str, user: str, client: str) -> dict[str, Any]:
    """
    Connect to Perforce and validate the pending changelist.

    Returns:
        {"pass": bool, "violations": [{"file", "reason"}]}
    """
    p4 = P4.P4()
    p4.port   = port
    p4.user   = user
    p4.client = client
    violations = []

    with p4.connect():
        opened = p4.run("opened")
        for f in opened:
            depot_file = f.get("depotFile", "")
            ext = "." + depot_file.rsplit(".", 1)[-1] if "." in depot_file else ""

            if ext in BLOCKED_EXTENSIONS:
                violations.append({"file": depot_file, "reason": f"Blocked extension: {ext}"})

            basename = depot_file.split("/")[-1]
            if not NAMING_PATTERN.match(basename):
                violations.append({"file": depot_file, "reason": f"Naming violation: {basename}"})

    return {"pass": len(violations) == 0, "violations": violations}


def setup_workspace(port: str, user: str, client: str, root: str, depot_path: str) -> dict[str, Any]:
    """
    Create or update a Perforce workspace (client spec).

    Args:
        port:       P4PORT  e.g. "ssl:perforce.studio.com:1666"
        user:       P4USER
        client:     Workspace name
        root:       Local root directory
        depot_path: Depot mapping e.g. "//depot/main/..."
    """
    p4 = P4.P4()
    p4.port   = port
    p4.user   = user
    p4.client = client

    with p4.connect():
        spec = p4.fetch_client(client)
        spec["Root"] = root
        spec["View"] = [f"{depot_path} //{client}/..."]
        p4.save_client(spec)

    return {"workspace": client, "root": root, "mapping": depot_path}
