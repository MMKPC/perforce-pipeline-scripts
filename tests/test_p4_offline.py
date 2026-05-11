"""
tests/test_p4_offline.py
Offline tests — mocks P4Python. No Perforce server needed.
Run with: pytest tests/
"""

import sys
import types
import unittest
from unittest.mock import patch


# ── P4 mock ───────────────────────────────────────────────────────────────────

class _P4Mock:
    port = ""
    user = ""
    client = ""

    def connect(self):     return self
    def __enter__(self):   return self
    def __exit__(self, *a): pass

    def run(self, *args):
        cmd = args[0]
        if cmd == "opened":
            return [
                {"depotFile": "//depot/main/Content/SM_Rock.uasset"},
                {"depotFile": "//depot/main/Content/SM_Wall.uasset"},
            ]
        if cmd == "sync":
            return [{"depotFile": "//depot/main/Content/SM_NewAsset.uasset",
                     "haveRev": "1", "headRev": "3"}]
        if cmd == "files":
            return []
        return []

    def fetch_client(self, client): return {"Root": "/mnt/workspace"}
    def save_client(self, spec):    pass


class _P4ExceptionMock(Exception):
    pass


def _install_p4_mock():
    p4_mod = types.ModuleType("P4")
    p4_mod.P4         = _P4Mock
    p4_mod.P4Exception = _P4ExceptionMock
    sys.modules["P4"] = p4_mod
    for k in list(sys.modules.keys()):
        if "p4_pipeline" in k:
            del sys.modules[k]


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSubmitHook(unittest.TestCase):

    def setUp(self):
        _install_p4_mock()
        import p4_pipeline.submit_hook as h
        self.h = h

    def test_valid_files_pass(self):
        result = self.h.run_pre_submit_check("server:1666", "user", "client")
        self.assertTrue(result["pass"])
        self.assertEqual(result["violations"], [])

    def test_blocked_extension_caught(self):
        # Patch the instance method via mock, not class attribute mutation
        _install_p4_mock()
        import p4_pipeline.submit_hook as h2
        with patch.object(sys.modules["P4"].P4, "run",
                          side_effect=lambda self_or_cmd, *a, **kw: (
                              [{"depotFile": "//depot/main/Content/junk.tmp"}]
                          )):
            result = h2.run_pre_submit_check("server:1666", "user", "client")
        self.assertFalse(result["pass"])
        self.assertTrue(any("tmp" in v["reason"] for v in result["violations"]))


class TestSyncReport(unittest.TestCase):

    def setUp(self):
        _install_p4_mock()
        import p4_pipeline.sync_report as s
        self.s = s

    def test_reports_out_of_date_files(self):
        result = self.s.sync_status("server:1666", "user", "client")
        self.assertEqual(result["out_of_date_count"], 1)
        self.assertEqual(result["out_of_date"][0]["head_rev"], "3")

    def test_no_locked_files(self):
        result = self.s.sync_status("server:1666", "user", "client")
        self.assertEqual(result["locked"], [])


if __name__ == "__main__":
    unittest.main()
