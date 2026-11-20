"""Music Production Blueprint v0: the example validates, and the semantic rules catch broken plans."""
import copy, importlib.util, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BP = os.path.join(ROOT, 'skill', 'faderhand', 'blueprint')
spec = importlib.util.spec_from_file_location('validate_blueprint', os.path.join(BP, 'validate_blueprint.py'))
vb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vb)
EXAMPLE = json.load(open(os.path.join(BP, 'examples', 'fixture-comprehension.blueprint.json')))


def errs(bp):
    return vb.validate(bp)[0]


def test_schema_file_is_json():
    s = json.load(open(vb.SCHEMA))
    assert s['title'] == 'Music Production Blueprint v0'


def test_example_is_valid():
    assert errs(EXAMPLE) == []


def test_unknown_role_is_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['sections'][0]['active_roles'].append('theremin')
    assert any('theremin' in e for e in errs(bp))


def test_overlapping_sections_are_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['sections'][1]['start_bar'] = 5
    assert any('overlap' in e for e in errs(bp))


def test_section_past_the_end_is_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['sections'][1]['length_bars'] = 40
    assert any('runs past' in e for e in errs(bp))


def test_missing_layer_target_is_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['tracks'][1]['layer_of'] = 'Nope'
    assert any('layers with missing' in e for e in errs(bp))


def test_unoffered_capability_is_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['execution']['needs'].append('time_travel')
    assert any('time_travel' in e for e in errs(bp))


def test_unused_role_is_a_warning_not_an_error():
    bp = copy.deepcopy(EXAMPLE)
    bp['roles'].append({'id': 'pad', 'function': 'texture', 'why': 'air above the keys'})
    e, w = vb.validate(bp)
    assert e == [] and any("'pad' has no track" in x for x in w)
