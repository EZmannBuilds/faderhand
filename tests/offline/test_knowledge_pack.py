"""The shipped knowledge pack: valid, complete, and limited to the kinds of lesson that may ship."""
import json
from pathlib import Path

PACK = Path(__file__).resolve().parents[2] / "skill" / "faderhand" / "knowledge"
REQUIRED = ("id", "concept", "knowledge_class", "validation_status", "interpretation", "technique", "limitations", "basis")


def _doc():
    return json.loads((PACK / "lessons.json").read_text(encoding="utf-8"))


def test_pack_schema_and_fields():
    doc = _doc()
    assert doc["schema"] == "faderhand.knowledge/1"
    assert doc["count"] == len(doc["lessons"]) > 0
    ids = [r["id"] for r in doc["lessons"]]
    assert len(ids) == len(set(ids))
    for r in doc["lessons"]:
        for k in REQUIRED:
            assert r.get(k), (r["id"], k)
        assert r["knowledge_class"] in ("established", "experimental_finding"), r["id"]
        assert r["validation_status"] == "supported", r["id"]
        if r["knowledge_class"] == "established":
            assert r.get("sources"), r["id"]


def test_pack_carries_no_private_fields():
    for r in _doc()["lessons"]:
        for k in ("context", "scope_person", "scope_project", "experiments", "audio_refs", "human_feedback", "source"):
            assert k not in r, (r["id"], k)


def test_markdown_lists_every_lesson():
    md = (PACK / "LESSONS.md").read_text(encoding="utf-8")
    for r in _doc()["lessons"]:
        assert r["id"] in md and r["concept"] in md
