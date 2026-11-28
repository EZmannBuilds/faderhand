"""export_audio, offline: the exporter it runs (tools/live_export.py, in its own uv environment with PyObjC), the
arguments it passes, and how it reports the exporter's answer or failure. The export itself needs Live and macOS
Accessibility; it was measured in Live (docs/CAPABILITY-MATRIX.md)."""
import importlib.util
import json
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_spec = importlib.util.spec_from_file_location("faderhand_srv", os.path.join(ROOT, "server", "ableton_tooling_server.py"))
srv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(srv)


class Done(object):
    def __init__(self, stdout="", stderr=""):
        self.stdout, self.stderr, self.returncode = stdout, stderr, 0


def test_the_exporter_ships_with_the_server():
    assert os.path.isfile(srv.EXPORTER)
    assert os.path.samefile(srv.EXPORTER, os.path.join(ROOT, "tools", "live_export.py"))


def test_command_line():
    cmd = srv._export_cmd("9.1.1", "8.0.0", "/tmp/x/Song.wav", {"Normalize": False, "Render as Loop": True})
    assert cmd[:3] == ["uv", "run", "-q"]
    for pkg in ("pyobjc-framework-ApplicationServices", "pyobjc-framework-Cocoa", "pyobjc-framework-Quartz"):
        assert pkg in cmd
    i = cmd.index(srv.EXPORTER)
    assert cmd[i + 1:] == ["--start", "9.1.1", "--length", "8.0.0", "--out", "/tmp/x/Song.wav",
                           "--option", "Normalize=off", "--option", "Render as Loop=on"]


def test_reports_the_exporters_json(monkeypatch):
    seen = {}

    def fake(cmd, **k):
        seen.update(cmd=cmd, timeout=k.get("timeout"))
        return Done(stdout="exporting...\n" + json.dumps({"ok": True, "path": "/tmp/x/Song.wav", "seconds": 13.7}))

    monkeypatch.setattr(subprocess, "run", fake)
    r = json.loads(srv.export_audio(start="1.1.1", length="4.0.0", path="/tmp/x/Song.wav", timeout=60))
    assert r == {"ok": True, "path": "/tmp/x/Song.wav", "seconds": 13.7}
    assert seen["timeout"] == 180.0 and seen["cmd"][-6:] == ["--start", "1.1.1", "--length", "4.0.0", "--out",
                                                            "/tmp/x/Song.wav"]


def test_a_failed_exporter_is_an_error_not_a_crash(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda cmd, **k: Done(stdout="", stderr="Traceback ...\nImportError: AppKit"))
    r = json.loads(srv.export_audio(start="1.1.1", length="4.0.0", path="/tmp/x/Song.wav"))
    assert r["ok"] is False and "exporter failed" in r["error"] and "AppKit" in r["error"]
