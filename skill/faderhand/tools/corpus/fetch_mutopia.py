"""Download a curated Mutopia selection (MIDI only) with licence and provenance.

Usage: python3 -I fetch_mutopia.py <corpus_root>
Writes <corpus_root>/mutopia/<id>_<slug>/... and <corpus_root>/mutopia/manifest.json.
Never executes anything it downloads. Zips are read with zipfile and only .mid/.midi members are written.
"""
import hashlib, html, io, json, os, re, sys, time, urllib.request, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutopia_picks import PICKS

UA = {"User-Agent": "Mozilla/5.0 (personal MIDI research corpus)"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()

def info(pid):
    h = get(f"https://www.mutopiaproject.org/cgibin/piece-info.cgi?id={pid}").decode("utf-8", "replace")
    t = html.unescape(re.sub(r"<[^>]+>", "|", re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)))
    t = re.sub(r"(\|\s*)+", "|", t)
    def field(name):
        m = re.search(r"\|" + re.escape(name) + r":\|([^|]*)", t)
        return m.group(1).strip() if m else None
    head = re.match(r"\|([^|]*), by ([^|]*)\|", t)
    mids = re.findall(r'href="([^"]+(?:\.mid|\.midi|-mids\.zip))"', h)
    return {
        "mutopia_id": pid, "title": head.group(1) if head else None, "composer": head.group(2) if head else None,
        "instruments": field("Instrument(s)"), "style": field("Style"), "opus": field("Opus"),
        "date_of_composition": field("Date of composition"), "edition_source": field("Source"),
        "licence": field("Copyright"), "music_id": field("Music ID Number"), "maintainer": field("Maintainer"),
        "page": f"https://www.mutopiaproject.org/cgibin/piece-info.cgi?id={pid}", "midi_url": mids[0] if mids else None,
    }

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s or "untitled").strip("-")[:60]

def main(root):
    out = os.path.join(root, "mutopia"); os.makedirs(out, exist_ok=True)
    man_path = os.path.join(out, "manifest.json")
    manifest = json.load(open(man_path)) if os.path.exists(man_path) else {}
    for pid, why in PICKS.items():
        if str(pid) in manifest and manifest[str(pid)].get("files"):
            continue
        rec = info(pid); rec["why_selected"] = why; rec["files"] = []; rec["status"] = "ok"
        if not rec["midi_url"]:
            rec["status"] = "no MIDI offered"; manifest[str(pid)] = rec; continue
        d = os.path.join(out, f"{pid}_{slug(rec['title'])}"); os.makedirs(d, exist_ok=True)
        try:
            data = get(rec["midi_url"])
        except Exception as e:
            rec["status"] = f"download failed: {e}"; manifest[str(pid)] = rec; continue
        rec["download_sha256"] = hashlib.sha256(data).hexdigest()
        members = []
        if rec["midi_url"].endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    base = os.path.basename(n)
                    if base and base.lower().endswith((".mid", ".midi")) and ".." not in n:
                        members.append((base, z.read(n)))
        else:
            members.append((os.path.basename(rec["midi_url"]), data))
        for name, blob in members:
            p = os.path.join(d, name)
            with open(p, "wb") as f: f.write(blob)
            rec["files"].append({"path": os.path.relpath(p, root), "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)})
        manifest[str(pid)] = rec
        json.dump(manifest, open(man_path, "w"), indent=1, ensure_ascii=False)
        time.sleep(0.7)
    json.dump(manifest, open(man_path, "w"), indent=1, ensure_ascii=False)
    print(len(manifest), "pieces;", sum(len(r["files"]) for r in manifest.values()), "MIDI files")

if __name__ == "__main__":
    main(sys.argv[1])
