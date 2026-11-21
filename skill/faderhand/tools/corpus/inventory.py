"""Inventory, licence status, dedup and held-out split for the MIDI corpus.

Usage (Python 3.10+, mido):
  uv run --no-project --with mido python -I inventory.py <corpus_root> [--workers 2]

Writes <corpus_root>/_inventory/inventory.jsonl (one row per file), duplicates and a summary.
Approval policy (see tools/PROVENANCE.md in the Faderhand skill):
  groove   approved        CC BY 4.0 (Google LLC); held-out = the dataset's own "test" split
  mutopia  approved        Public Domain / CC BY / CC BY-SA per piece; held-out = ~12% of pieces by hash
  pdmx     approved only if no licence conflict, PDMX-deduplicated, and either classical/folk/sacred
           or marked original; everything else is excluded (possible arrangement of a copyrighted work)
Only these cleared sources are inventoried. Material that is not cleared for building software is not read.
"""
import argparse, csv, hashlib, json, os, sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_lib  # noqa: E402

SAFE_PDMX_GENRES = {"classical", "folk", "religiousmusic"}


def h(s, mod):
    return int(hashlib.sha1(s.encode()).hexdigest(), 16) % mod


def collect(root):
    rows = []
    # Groove
    gdir = os.path.join(root, "groove", "groove")
    for r in csv.DictReader(open(os.path.join(gdir, "info.csv"))):
        rows.append({"source": "groove", "rel": f"groove/groove/{r['midi_filename']}", "licence": "CC BY 4.0",
                     "status": "approved", "holdout": r["split"] == "test",
                     "meta": {"drummer": r["drummer"], "style": r["style"], "bpm": float(r["bpm"]),
                              "beat_type": r["beat_type"], "meter": r["time_signature"], "split": r["split"]}})
    # Mutopia
    man = json.load(open(os.path.join(root, "mutopia", "manifest.json")))
    for pid, rec in man.items():
        for f in rec["files"]:
            rows.append({"source": "mutopia", "rel": f["path"], "licence": rec["licence"], "status": "approved",
                         "holdout": h("mutopia" + pid, 100) < 12,
                         "meta": {k: rec[k] for k in ("mutopia_id", "title", "composer", "instruments", "style",
                                                       "date_of_composition", "page", "maintainer", "why_selected")}})
    # PDMX
    csv.field_size_limit(10**9)
    for r in csv.DictReader(open(os.path.join(root, "pdmx", "PDMX.csv"))):
        genres = set((r["genres"] or "NA").split("-")) - {"NA"}
        conflict_free = r["subset:no_license_conflict"] == "True"
        dedup = r["subset:deduplicated"] == "True"
        original = r["is_original"] == "True"
        if not conflict_free:
            status = "excluded: licence conflict flagged by PDMX"
        elif not dedup:
            status = "excluded: duplicate within PDMX"
        elif (genres and genres <= SAFE_PDMX_GENRES) or (original and not genres):
            status = "approved"
        else:
            status = "excluded: may arrange a copyrighted work (genre %s)" % ("-".join(sorted(genres)) or "NA")
        rel = "pdmx/" + r["mid"].lstrip("./")
        rows.append({"source": "pdmx", "rel": rel, "licence": r["license"], "status": status,
                     "holdout": h(rel, 100) < 5,
                     "meta": {"genres": sorted(genres), "is_original": original, "title": r["title"],
                              "composer": r["composer_name"], "rating": r["rating"], "n_tracks": r["n_tracks"],
                              "licence_url": r["license_url"]}})
    return rows


def probe(args):
    root, row, parse = args
    p = os.path.join(root, row["rel"])
    out = {"exists": os.path.exists(p)}
    if not out["exists"]:
        return out
    blob = open(p, "rb").read()
    out["sha256"] = hashlib.sha256(blob).hexdigest()
    out["bytes"] = len(blob)
    if parse:
        try:
            s = midi_lib.read(p)
            ex, tr = midi_lib.content_hashes(s)
            out.update(readable=True, n_notes=len(s.notes), ppq=s.ppq, bpm=round(s.bpm, 2),
                       meter=f"{s.meter[0]}/{s.meter[1]}", music_hash=ex, transpose_hash=tr,
                       seconds=round(max((n.end_s for n in s.notes), default=0), 2))
        except Exception as e:  # noqa: BLE001
            out.update(readable=False, error=str(e)[:200])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    root = a.root
    rows = collect(root)
    # Parse every non-PDMX file, and approved PDMX files; others get hashed and checked for existence.
    jobs = [(root, r, r["source"] != "pdmx" or r["status"] == "approved") for r in rows]
    with ProcessPoolExecutor(max_workers=min(2, a.workers)) as ex:
        for r, res in zip(rows, ex.map(probe, jobs, chunksize=200)):
            r.update(res)
    # Dedup: exact bytes, then musical content, then transposition.
    seen_sha, seen_mus, seen_tr = {}, {}, {}
    for r in rows:
        if not r.get("exists"):
            continue
        key = r["sha256"]
        if key in seen_sha:
            r["duplicate_of"] = seen_sha[key]
            continue
        seen_sha[key] = r["rel"]
        if r.get("music_hash") and r.get("n_notes"):
            if r["music_hash"] in seen_mus:
                r["same_music_as"] = seen_mus[r["music_hash"]]
            else:
                seen_mus[r["music_hash"]] = r["rel"]
                if r["transpose_hash"] in seen_tr:
                    r["transposition_of"] = seen_tr[r["transpose_hash"]]
                else:
                    seen_tr[r["transpose_hash"]] = r["rel"]
    out = os.path.join(root, "_inventory")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "inventory.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {}
    for r in rows:
        s = summary.setdefault(r["source"], {"files": 0, "missing": 0, "unreadable": 0, "byte_duplicates": 0,
                                             "same_music": 0, "transpositions": 0, "status": {}, "holdout": 0})
        s["files"] += 1
        s["missing"] += not r.get("exists")
        s["unreadable"] += r.get("readable") is False
        s["byte_duplicates"] += "duplicate_of" in r
        s["same_music"] += "same_music_as" in r
        s["transpositions"] += "transposition_of" in r
        s["holdout"] += bool(r["holdout"])
        s["status"][r["status"]] = s["status"].get(r["status"], 0) + 1
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
