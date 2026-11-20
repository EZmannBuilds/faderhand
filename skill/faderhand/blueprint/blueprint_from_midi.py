"""Express an existing song as a Music Production Blueprint v0, from its MIDI plus a small mapping file.

usage: uv run -q --no-project --with mido python blueprint_from_midi.py <song.mid> <mapping.json> <out.json>

The mapping says what the analyser can't know:
  {"title", "style", "key", "brief", "focal_element", "contrast", "mood": [...],
   "roles": [{"id", "function", "why", "source": {"midi_track": "Drums", "pitches": [36]}}],
   "tracks": [{"name", "roles": [...], "instrument": {...}, "layer_of", "relative_db", "effects", "midi_track"}],
   "relationships": [{"roles": ["kick", "low_808"], "rule": "coordinate_onsets", "note": "..."}],
   "section_ids": {"Intro": "intro", ...} (optional), "execution": {...}}
Measured from the MIDI: sections (from marker events), which roles are active in each section, energy (note
density, scaled 0.1-1 against the busiest section), what changed from the previous section, the gesture in the bar
before (fill, drop or stop), and each relationship's value:
  coordinate_onsets  share of the first role's onsets within 1/32 of the second's
  avoid_onsets       share of the first role's onsets NOT within 1/32 of the second's
  register_separation  median pitch of the first minus median pitch of the second (semitones)
"""
import bisect, json, os, re, statistics as st, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools', 'corpus'))
import midi_lib  # noqa: E402
import mido  # noqa: E402


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_') or 'section'


def main(midi_path, map_path, out_path):
    M = json.load(open(map_path))
    song = midi_lib.read(midi_path)
    ppq = song.ppq
    bar = song.bar_ticks()
    nbars = max(n.end for n in song.notes) // bar + 1
    names = {t: n for t, n in song.track_names.items()}
    by_track = defaultdict(list)
    for n in song.notes:
        by_track[names.get(n.track, str(n.track))].append(n)
    # markers -> sections
    marks = []
    for tr in mido.MidiFile(midi_path).tracks:
        t = 0
        for m in tr:
            t += m.time
            if m.is_meta and m.type == 'marker':
                marks.append((t, m.text))
    marks.sort()
    if M.get('sections'):   # the mapping can name sections when the MIDI has no markers
        marks = [((sec['start_bar'] - 1) * bar, sec['name']) for sec in M['sections']]
    if not marks:
        marks = [(0, 'Song')]
    sec_ids = M.get('section_ids', {})
    sections = []
    for i, (t, name) in enumerate(marks):
        start = t // bar + 1
        end = (marks[i + 1][0] // bar + 1) if i + 1 < len(marks) else nbars + 1
        sections.append({'id': sec_ids.get(name, slug(name)), 'name': name, 'start_bar': int(start), 'length_bars': int(end - start)})
    # role notes
    role_notes = {}
    for r in M['roles']:
        src = r.get('source', {})
        ns = by_track.get(src.get('midi_track'), [])
        if src.get('pitches'):
            ns = [n for n in ns if n.pitch in set(src['pitches'])]
        role_notes[r['id']] = ns
    # activity, energy, changes, gestures
    dens = []
    for s in sections:
        t0, t1 = (s['start_bar'] - 1) * bar, (s['start_bar'] - 1 + s['length_bars']) * bar
        act = [rid for rid, ns in role_notes.items() if sum(1 for n in ns if t0 <= n.start < t1) >= 2]
        s['active_roles'] = act
        dens.append(sum(1 for n in song.notes if t0 <= n.start < t1) / s['length_bars'])
    mx = max(dens) or 1
    drum_track = M.get('drum_midi_track', 'Drums')
    dbar = Counter(n.start // bar for n in by_track.get(drum_track, []))
    med = st.median([dbar.get(b, 0) for b in range(nbars)]) if nbars else 0
    prev = None
    for s, d in zip(sections, dens):
        s['energy'] = round(0.1 + 0.9 * d / mx, 2)
        if prev:
            added = sorted(set(s['active_roles']) - set(prev['active_roles']))
            removed = sorted(set(prev['active_roles']) - set(s['active_roles']))
            ch = []
            if added: ch.append('adds ' + ', '.join(added))
            if removed: ch.append('drops ' + ', '.join(removed))
            de = s['energy'] - prev['energy']
            if abs(de) >= 0.1: ch.append('energy %s %.2f' % ('up' if de > 0 else 'down', abs(de)))
            s['changes'] = ch
            b = s['start_bar'] - 2  # the bar before, 0-based
            c = dbar.get(b, 0)
            sig = lambda bb: tuple(sorted({(n.pitch, round((n.start - bb * bar) / (ppq / 4))) for n in by_track.get(drum_track, []) if n.start // bar == bb}))
            p0 = prev['start_bar'] - 1
            usual = Counter(sig(x) for x in range(p0, b)).most_common(1)
            if med and c >= 1.3 * med: s['gesture_before'] = 'drum fill (%d hits against a median of %d)' % (c, med)
            elif med and c <= 0.4 * med: s['gesture_before'] = 'drop or stop in the drums'
            elif usual and sig(b) != usual[0][0] and c:
                s['gesture_before'] = 'drum variation: the bar before differs from the section\'s usual bar'
        prev = s
    # relationships
    tol = ppq / 8  # 1/32 note
    rels = []
    for rel in M.get('relationships', []):
        a, b = rel['roles'][:2]
        A, B = role_notes.get(a, []), role_notes.get(b, [])
        out = dict(rel)
        if A and B:
            bon = sorted({n.start for n in B})
            def near(t):
                i = bisect.bisect_left(bon, t)
                return any(0 <= j < len(bon) and abs(bon[j] - t) <= tol for j in (i - 1, i))
            aon = sorted({n.start for n in A})
            if rel['rule'] == 'coordinate_onsets':
                out['measured'] = {'metric': 'share of %s onsets within 1/32 of %s' % (a, b), 'value': round(sum(map(near, aon)) / len(aon), 3)}
            elif rel['rule'] == 'avoid_onsets':
                out['measured'] = {'metric': 'share of %s onsets clear of %s' % (a, b), 'value': round(1 - sum(map(near, aon)) / len(aon), 3)}
            elif rel['rule'] == 'register_separation':
                out['measured'] = {'metric': 'median pitch %s minus %s (semitones)' % (a, b),
                                   'value': float(st.median(n.pitch for n in A) - st.median(n.pitch for n in B))}
        rels.append(out)
    roles = []
    for r in M['roles']:
        ns = role_notes[r['id']]
        rr = {k: r[k] for k in ('id', 'function', 'why')}
        if ns and r['function'] not in ('rhythm', 'percussion'):
            rr['register'] = [min(n.pitch for n in ns), max(n.pitch for n in ns)]
        roles.append(rr)
    bp = {
        'schema_version': '0.1',
        'song': {k: v for k, v in (('title', M['title']), ('style', M.get('style')), ('tempo_bpm', round(song.bpm, 2)),
                                    ('meter', '%d/%d' % song.meter), ('key', M.get('key')), ('length_bars', int(nbars)),
                                    ('mode', M.get('mode', 'instrumental'))) if v is not None},
        'creative_direction': {k: M[k] for k in ('focal_element', 'contrast', 'mood', 'avoid', 'brief') if k in M},
        'roles': roles,
        'tracks': M['tracks'],
        'sections': sections,
        'relationships': rels,
        'techniques': M.get('techniques', []),
        'execution': M.get('execution', {'daw': 'ableton_live'}),
        'provenance': {'created_by': 'blueprint_from_midi.py', 'source': os.path.basename(midi_path),
                       'version': M.get('version', 'v0'), 'notes': 'Sections, activity, energy, changes, gestures and relationship values are measured from the MIDI; roles, tracks and intent come from the mapping file.'},
    }
    json.dump(bp, open(out_path, 'w'), indent=1, ensure_ascii=False)
    print('wrote', out_path, '|', len(roles), 'roles,', len(M['tracks']), 'tracks,', len(sections), 'sections')


if __name__ == '__main__':
    main(*sys.argv[1:4])
