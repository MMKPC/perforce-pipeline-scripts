"""
p4_pipeline/sync_report.py
Reports workspace sync status — what's out of date, what's locked.
"""

from __future__ import annotations
from typing import Any

try:
    import P4
except ImportError:
    raise ImportError("Install P4Python: pip install p4python")


def sync_status(port: str, user: str, client: str, depot_path: str = "//...") -> dict[str, Any]:
    """
    List files that are out of date vs head revision.
    Dry-run only — does NOT sync.
    """
    p4 = P4.P4()
    p4.port   = port
    p4.user   = user
    p4.client = client

    out_of_date = []
    locked      = []

    with p4.connect():
        # sync -n = preview only
        try:
            preview = p4.run("sync", "-n", depot_path)
            for f in preview:
                out_of_date.append({
                    "file"     : f.get("depotFile", ""),
                    "have_rev" : f.get("haveRev", "0"),
                    "head_rev" : f.get("headRev", "?"),
                })
        except P4.P4Exception:
            pass

        try:
            files = p4.run("files", "-e", depot_path)
            for f in files:
                if f.get("action") in ("lock", "branch+l"):
                    locked.append(f.get("depotFile", ""))
        except P4.P4Exception:
            pass

    return {
        "out_of_date_count": len(out_of_date),
        "out_of_date"      : out_of_date,
        "locked"           : locked,
    }
