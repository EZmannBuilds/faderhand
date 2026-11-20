"""Validate a Music Production Blueprint v0: the JSON Schema, then the musical-structure rules the schema can't express.

usage: uv run -q --no-project --with jsonschema python validate_blueprint.py <blueprint.json> [--json]
Exit 0 when there are no errors (warnings are allowed), 1 otherwise.

Semantic rules:
  errors   unknown role referenced (track, section, relationship, technique); duplicate role/track/section ids;
           sections overlap or run past the song; a track layers with a track that doesn't exist;
           an execution need Faderhand doesn't offer
  warnings a role no track plays; a role never active; a track with no role justification; gaps between sections;
           a section that changes nothing from the one before; no gesture before a section change
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, 'music_blueprint.v0.schema.json')
# What the Faderhand executor can do today (keep in step with docs/CAPABILITY-MATRIX.md and daw/README.md)
FADERHAND_CAN = {
    'arrangement_midi_clips', 'session_clips', 'tracks', 'browser_load', 'device_parameters', 'mixer_db',
    'returns_and_sends', 'routing_and_buses', 'racks', 'drum_rack_chain_volume', 'sidechain', 'session_automation',
    'arrangement_automation_recording', 'render_main', 'render_by_solo', 'vital_patch_injection', 'midi_check',
}


def validate(bp):
    errors, warnings = [], []
    try:
        import jsonschema
        v = jsonschema.Draft202012Validator(json.load(open(SCHEMA)))
        for e in sorted(v.iter_errors(bp), key=lambda e: list(e.path)):
            errors.append('schema: %s: %s' % ('/'.join(map(str, e.path)) or '(root)', e.message))
    except ImportError:
        warnings.append('jsonschema not installed: schema not checked (run with --with jsonschema)')
    if errors:
        return errors, warnings
    roles = [r['id'] for r in bp['roles']]
    tracks = [t['name'] for t in bp['tracks']]
    sects = [s['id'] for s in bp['sections']]
    for kind, ids in (('role', roles), ('track', tracks), ('section', sects)):
        dup = {x for x in ids if ids.count(x) > 1}
        if dup:
            errors.append('duplicate %s ids: %s' % (kind, sorted(dup)))
    R = set(roles)
    for t in bp['tracks']:
        for r in t['roles']:
            if r not in R:
                errors.append('track %r plays unknown role %r' % (t['name'], r))
        if t.get('layer_of') and t['layer_of'] not in tracks:
            errors.append('track %r layers with missing track %r' % (t['name'], t['layer_of']))
    for s in bp['sections']:
        for r in s['active_roles']:
            if r not in R:
                errors.append('section %r activates unknown role %r' % (s['id'], r))
    for rel in bp.get('relationships', []):
        for r in rel['roles']:
            if r not in R:
                errors.append('relationship %s references unknown role %r' % (rel['rule'], r))
    for tq in bp.get('techniques', []):
        for r in tq.get('applied_to', []):
            if r not in R:
                errors.append('technique %r applied to unknown role %r' % (tq['id'], r))
    for need in bp.get('execution', {}).get('needs', []):
        if need not in FADERHAND_CAN:
            errors.append('execution need %r is not something Faderhand offers' % need)
    # sections: order, overlap, gaps, length
    ss = sorted(bp['sections'], key=lambda s: s['start_bar'])
    end_bar = bp['song']['length_bars'] + 1
    for a, b in zip(ss, ss[1:]):
        a_end = a['start_bar'] + a['length_bars']
        if a_end > b['start_bar']:
            errors.append('sections %r and %r overlap' % (a['id'], b['id']))
        elif a_end < b['start_bar']:
            warnings.append('gap of %d bars between %r and %r' % (b['start_bar'] - a_end, a['id'], b['id']))
        if set(a['active_roles']) == set(b['active_roles']) and not b.get('changes'):
            warnings.append('section %r changes nothing from %r (same roles, no changes listed)' % (b['id'], a['id']))
        if not b.get('gesture_before'):
            warnings.append('no gesture before section %r' % b['id'])
    if ss and ss[-1]['start_bar'] + ss[-1]['length_bars'] > end_bar:
        errors.append('section %r runs past the song (%d bars)' % (ss[-1]['id'], bp['song']['length_bars']))
    played = {r for t in bp['tracks'] for r in t['roles']}
    active = {r for s in bp['sections'] for r in s['active_roles']}
    for r in bp['roles']:
        if r['id'] not in played:
            warnings.append('role %r has no track' % r['id'])
        if r['id'] not in active:
            warnings.append('role %r is never active' % r['id'])
    return errors, warnings


def main():
    bp = json.load(open(sys.argv[1]))
    errors, warnings = validate(bp)
    if '--json' in sys.argv:
        print(json.dumps({'valid': not errors, 'errors': errors, 'warnings': warnings}, indent=1))
    else:
        print('%s: %s' % (os.path.basename(sys.argv[1]), 'VALID' if not errors else 'INVALID'))
        for e in errors:
            print('  ERROR  ', e)
        for w in warnings:
            print('  warning', w)
        print('%d roles, %d tracks, %d sections, %d relationships' % (
            len(bp.get('roles', [])), len(bp.get('tracks', [])), len(bp.get('sections', [])), len(bp.get('relationships', []))))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
