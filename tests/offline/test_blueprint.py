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


# --- 0.2 extensions: role states, events, preservation ---------------------------------------------

def v02():
    bp = copy.deepcopy(EXAMPLE)
    bp['schema_version'] = '0.2'
    return bp


def test_role_state_must_match_active_roles():
    bp = v02()
    bp['sections'][0]['role_states'] = [{'role': 'keys', 'state': 'silent'}]   # keys is active in the verse
    assert any('silent but listed as active' in e for e in errs(bp))


def test_role_state_layers_must_belong_to_the_role():
    bp = v02()
    bp['sections'][1]['role_states'] = [{'role': 'lead_hook', 'state': 'reduced', 'active_layers': ['Bass']}]
    assert any('is not a layer' in e for e in errs(bp))


def test_event_outside_the_section_is_an_error():
    bp = v02()
    bp['sections'][0]['events'] = [{'type': 'fill', 'at_bar': 8, 'length_beats': 8}]
    assert any('runs outside the section' in e for e in errs(bp))


def test_valid_v02_extensions_pass():
    bp = v02()
    bp['sections'][1]['role_states'] = [{'role': 'lead_hook', 'state': 'featured', 'reason': 'the hook arrives'}]
    bp['sections'][0]['events'] = [{'type': 'pre_transition', 'at_bar': 8, 'length_beats': 4, 'roles': ['hats'],
                                    'target_section': 'hook'}]
    bp['sections'][1]['energy_strategy'] = {'rhythm': 'up', 'density': 'up', 'register': 'same'}
    bp['preservation'] = [{'what': 'groove', 'roles': ['kick', 'bass'], 'rule': 'frozen', 'reason': 'approved'}]
    assert errs(bp) == []
