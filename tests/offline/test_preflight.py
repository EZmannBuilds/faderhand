"""Acoustic preflight: it flags note-off-ignoring samplers and long tails in a Set, finds existing fills in MIDI,
and catches a stem that sounds where no note is (and a note with no sound)."""
import gzip, importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, 'skill', 'faderhand', 'tools')
spec = importlib.util.spec_from_file_location('preflight', os.path.join(TOOLS, 'preflight.py'))
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

ALS = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton><LiveSet><Tracks>
 <MidiTrack Id="1"><Name><EffectiveName Value="Stabs" /></Name><DeviceChain>
  <Mixer><Speaker><Manual Value="true" /></Speaker><Sends>
   <TrackSendHolder Id="0"><Send><Manual Value="0.5" /></Send></TrackSendHolder></Sends></Mixer>
  <DeviceChain><Devices>
   <MultiSampler Id="0"><UserName Value="Strings Legato" />
    <VolumeAndPan><Envelope><LoopMode><LomId Value="0" /><Manual Value="4" /></LoopMode>
     <ReleaseTime><LomId Value="0" /><Manual Value="700" /></ReleaseTime></Envelope></VolumeAndPan>
    <Globals><NumVoices Value="5" /></Globals>
   </MultiSampler></Devices></DeviceChain></DeviceChain></MidiTrack>
 <MidiTrack Id="2"><Name><EffectiveName Value="Keys" /></Name><DeviceChain>
  <Mixer><Speaker><Manual Value="true" /></Speaker><Sends>
   <TrackSendHolder Id="0"><Send><Manual Value="0.0003" /></Send></TrackSendHolder></Sends></Mixer>
  <DeviceChain><Devices>
   <MultiSampler Id="0"><UserName Value="Piano" />
    <VolumeAndPan><Envelope><LoopMode><LomId Value="0" /><Manual Value="0" /></LoopMode>
     <ReleaseTime><LomId Value="0" /><Manual Value="300" /></ReleaseTime></Envelope></VolumeAndPan>
    <Globals><NumVoices Value="16" /></Globals>
   </MultiSampler></Devices></DeviceChain></DeviceChain></MidiTrack>
 <ReturnTrack Id="3"><Name><EffectiveName Value="A-Reverb" /></Name><DeviceChain><DeviceChain><Devices>
  <Reverb Id="0"><DecayTime><LomId Value="0" /><Manual Value="6000" /></DecayTime></Reverb>
 </Devices></DeviceChain></DeviceChain></ReturnTrack>
</Tracks></LiveSet></Ableton>"""


def test_set_flags_trigger_mode_and_reverb_send(tmp_path):
    p = tmp_path / 'song.als'
    with gzip.open(p, 'wb') as f:
        f.write(ALS.encode())
    r = pf.inspect_set(str(p))
    stabs = [t for t in r['tracks'] if t['track'] == 'Stabs'][0]
    assert stabs['instrument']['loop_mode'] == 'trigger' and stabs['sends_up'] == ['A-Reverb']
    assert any('Stabs' in f and 'Trigger' in f for f in r['flags'])
    assert any('A-Reverb' in f for f in r['flags'])
    assert not any(f.startswith('Keys') for f in r['flags'])


def _drum_midi(path):
    import mido
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack(); mf.tracks.append(tr)
    tr.append(mido.MetaMessage('track_name', name='Drums', time=0))
    ev = []
    for bar in range(8):
        for k in range(16):
            ev.append((bar * 1920 + k * 120, 42))
        if bar == 3:   # a snare run on the last beat of bar 4, same hit count
            ev += [(bar * 1920 + 1440 + k * 120, 38) for k in range(4)]
            ev = [e for e in ev if not (e[1] == 42 and bar * 1920 + 1440 <= e[0] < bar * 1920 + 1920)]
        if bar == 6:   # a drop
            ev = [e for e in ev if not (bar * 1920 + 240 <= e[0] < bar * 1920 + 1920)]
    t = 0
    for at, p in sorted(ev):
        tr.append(mido.Message('note_on', channel=9, note=p, velocity=90, time=at - t)); t = at
        tr.append(mido.Message('note_off', channel=9, note=p, velocity=0, time=60)); t += 60
    mf.save(path)


def test_gestures_find_snare_run_fill_and_drop(tmp_path):
    p = str(tmp_path / 'd.mid')
    _drum_midi(p)
    r = pf.gestures(p)
    assert 4 in r['fill_bars']
    assert 7 in r['drop_bars']


def test_occupancy_catches_tail_and_silent_note(tmp_path):
    import mido, numpy as np, soundfile as sf
    mf = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack(); mf.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
    tr.append(mido.MetaMessage('track_name', name='Stabs', time=0))
    for beat in (0, 8):                      # notes on beats 1 and 9, half a beat long
        tr.append(mido.Message('note_on', note=60, velocity=90, time=beat * 480 - (0 if beat == 0 else 240)))
        tr.append(mido.Message('note_off', note=60, velocity=0, time=240))
    mp = str(tmp_path / 's.mid'); mf.save(mp)
    sr, spb = 48000, 0.5
    x = np.zeros(int(12 * spb * sr))
    t = np.arange(int(0.25 * sr)) / sr
    x[:len(t)] = 0.3 * np.sin(2 * np.pi * 440 * t)                 # the first note sounds
    i = int(4 * spb * sr); x[i:i + int(spb * sr)] = 0.3 * np.sin(2 * np.pi * 440 * np.arange(int(spb * sr)) / sr)  # beat 5: sound, no note
    wp = str(tmp_path / 's.wav'); sf.write(wp, np.stack([x, x], 1), sr)   # beat 9: note, no sound
    r = pf.occupancy(wp, mp, 'Stabs')
    assert [b['beat'] for b in r['audible_without_notes']] == [5]
    assert [b['beat'] for b in r['notes_without_sound']] == [9]
