# Faderhand extensions (Phase 2): commands that can be re-imported with `reload_extensions`, no Live restart.
# Each command is a function cmd_<name>(cs, **params), where cs is the running Faderhand control surface:
# cs._song, cs._track(ref), cs._ref(track), cs._device(track, device, chain), cs._param(device, name),
# cs._set_param(param, value, units), cs._pout(param), cs._require_scratch(), cs.application().
# Runs on Live's main thread (the core's dispatcher schedules it). Raise ToolError for a clear, expected failure.
from __future__ import absolute_import, print_function, unicode_literals

import math
import random

EXT_VERSION = "0.7.0"


class ToolError(Exception):
    pass


# ---------------------------------------------------------------------------------------------- capability probe
def _resolve(cs, path):
    """'song', 'song.view', 'app', 'browser', 'track:N' / 'return:A' / 'master' / a name, then '/'-separated steps:
    'slot:S' (clip slot), 'clip:S' (session clip), 'aclip:I' (arrangement clip I), 'device:D', 'chain:C',
    'param:P' (index or name), 'mixer', 'envelope:P' (session clip envelope for device param P, via clip),
    'attr:NAME' (any attribute), 'item:N' (element N of a list, e.g. song/attr:groove_pool/attr:grooves/item:0),
    'child:NAME' (a browser item's child by name, e.g. browser/attr:packs/child:Core Library)."""
    parts = [p for p in str(path).split("/") if p]
    head = parts.pop(0) if parts else "song"
    if head == "song":
        obj = cs._song
    elif head == "song.view":
        obj = cs._song.view
    elif head == "app":
        obj = cs.application()
    elif head == "browser":
        obj = cs.application().browser
    else:
        obj = cs._track(head)
    for step in parts:
        key, _, arg = step.partition(":")
        if key == "slot":
            obj = list(obj.clip_slots)[int(arg)]
        elif key == "clip":
            obj = list(obj.clip_slots)[int(arg)].clip
            if obj is None:
                raise ToolError("no clip in slot %s" % arg)
        elif key == "aclip":
            obj = list(obj.arrangement_clips)[int(arg)]
        elif key == "device":
            ds = list(obj.devices)
            obj = ds[int(arg)] if arg.isdigit() else [d for d in ds if d.name == arg][0]
        elif key == "chain":
            obj = list(obj.chains)[int(arg)]
        elif key == "param":
            ps = list(obj.parameters)
            obj = ps[int(arg)] if arg.isdigit() else [p for p in ps if p.name == arg][0]
        elif key == "mixer":
            obj = obj.mixer_device
        elif key == "attr":
            obj = getattr(obj, arg)
        elif key == "item":
            seq = list(obj)
            if not 0 <= int(arg) < len(seq):
                raise ToolError("item %s out of range (%d)" % (arg, len(seq)))
            obj = seq[int(arg)]
        elif key == "child":
            match = [c for c in obj.children if c.name == arg]
            if not match:
                raise ToolError("no child %r; children: %s" % (arg, [c.name for c in obj.children][:60]))
            obj = match[0]
        else:
            raise ToolError("unknown path step %r" % step)
    return obj


def cmd_probe(cs, path="song", values=True):
    """Read-only capability detection: list the public attributes Live exposes on one LOM object, with simple
    values. Used to decide what this Live version supports before a command relies on it."""
    obj = _resolve(cs, path)
    out = {}
    for name in dir(obj):
        if name.startswith("_") or name.endswith("_has_listener") or name.startswith("add_") and name.endswith(
                "_listener") or name.startswith("remove_") and name.endswith("_listener"):
            continue
        try:
            v = getattr(obj, name)
        except Exception as e:
            out[name] = "<error %s>" % type(e).__name__
            continue
        if callable(v):
            doc = (getattr(v, "__doc__", "") or "").strip().split("\n")[0][:160]
            out[name] = "method: " + doc
        elif not values:
            out[name] = type(v).__name__
        elif isinstance(v, (bool, int, float)) or v is None:
            out[name] = v
        elif isinstance(v, str):
            out[name] = v[:120]
        else:
            out[name] = "<%s>" % type(v).__name__
    return {"path": path, "type": type(obj).__name__, "attributes": out}


# ---------------------------------------------------------------------------------------------- musical time
def _beats_per_bar(cs):
    return cs._song.signature_numerator * 4.0 / cs._song.signature_denominator


def _beats(cs, pos):
    """A position in beats (quarter notes, clip-local). Numbers are beats. Strings are 'bar.beat.sixteenth', 1-based
    ('1.1.1' = 0, '7.1.1' = start of bar 7), or 'Nb' for N beats. Computed from integers, so no drift."""
    if isinstance(pos, (int, float)) and not isinstance(pos, bool):
        return float(pos)
    s = str(pos).strip()
    if s.endswith("b"):
        return float(s[:-1])
    parts = [float(x) for x in s.split(".")]
    while len(parts) < 3:
        parts.append(1.0)
    bar, beat, six = parts[:3]
    if bar < 1 or beat < 1 or six < 1:
        raise ToolError("positions are 1-based bar.beat.sixteenth: %r" % pos)
    beat_len = 4.0 / cs._song.signature_denominator
    return (bar - 1) * _beats_per_bar(cs) + (beat - 1) * beat_len + (six - 1) * 0.25


# ---------------------------------------------------------------------------------------------- automation targets
def _target_param(cs, track, target):
    """target: {"mixer": "volume"|"pan"|"send"|"activator", "send": "A"} or
    {"device": ref, "chain": "c/d/c", "chain_device": n, "parameter": name or index}."""
    t = cs._track(track)
    if not isinstance(target, dict):
        raise ToolError("target must be an object, e.g. {'mixer': 'volume'} or {'device': 0, 'parameter': 'Freq'}")
    if "mixer" in target:
        m = t.mixer_device
        k = target["mixer"]
        if k == "volume":
            return t, m.volume
        if k == "pan":
            return t, m.panning
        if k == "activator":
            return t, m.track_activator
        if k == "send":
            return t, list(m.sends)[cs._send_index(target.get("send"))]
        raise ToolError("mixer target is volume, pan, send or activator, not %r" % k)
    d = cs._device(t, target.get("device", 0))
    if target.get("chain") not in (None, ""):
        d = cs._device(t, target.get("device", 0), target["chain"])[int(target.get("chain_device") or 0)]
    return t, cs._param(d, target["parameter"])


def _to_raw(cs, p, value, units):
    if units == "raw" or (units == "auto" and not isinstance(value, str)):
        v = float(value)
        if not p.min - 1e-9 <= v <= p.max + 1e-9:
            raise ToolError("%r outside %s's raw range %g..%g" % (value, p.name, p.min, p.max))
        return v
    if isinstance(value, str) and p.is_quantized:
        items = [str(i).lower() for i in p.value_items]
        if value.strip().lower() not in items:
            raise ToolError("%r is not a value of %s: %s" % (value, p.name, list(p.value_items)))
        return float(p.min + items.index(value.strip().lower()))
    target = cs._num(value) if isinstance(value, str) else float(value)
    if target is None:
        raise ToolError("cannot read a number from %r" % value)
    if target == float("-inf"):
        return float(p.min)
    return float(cs._bisect(p, target))


def _clip(cs, track, slot):
    t = cs._track(track)
    slots = list(t.clip_slots)
    if not 0 <= int(slot) < len(slots) or slots[int(slot)].clip is None:
        raise ToolError("no session clip in %s slot %s" % (cs._ref(t), slot))
    return t, slots[int(slot)].clip


def _envelope(cs, track, slot, target, create=False):
    t, clip = _clip(cs, track, slot)
    pt, p = _target_param(cs, track, target)
    env = clip.automation_envelope(p)
    if env is None and create:
        env = clip.create_automation_envelope(p)
    return t, clip, p, env


def _read(p, env, beat):
    v = env.value_at_time(beat + 1e-4)   # on a breakpoint border value_at_time returns the value before it
    return {"beat": round(beat, 6), "raw": round(float(v), 6), "display": p.str_for_value(v)}


# ---------------------------------------------------------------------------------------------- automation commands
def cmd_list_automatable_parameters(cs, track, slot=None):
    """Every parameter a session clip on this track can automate: mixer (volume, pan, sends) and each device's
    parameters, racks included (with the chain path to reach them). With slot, marks which have an envelope."""
    t = cs._track(track)
    clip = _clip(cs, track, slot)[1] if slot is not None else None
    out = []

    def add(p, target):
        row = {"target": target, "name": p.name, "min": p.min, "max": p.max, "display": p.str_for_value(p.value),
               "quantized": bool(p.is_quantized), "enabled": bool(p.is_enabled)}
        if clip is not None:
            row["has_envelope"] = clip.automation_envelope(p) is not None
        out.append(row)

    m = t.mixer_device
    add(m.volume, {"mixer": "volume"})
    add(m.panning, {"mixer": "pan"})
    for i, s in enumerate(m.sends):
        add(s, {"mixer": "send", "send": "ABCDEFGHIJKL"[i]})

    # top-level devices, then their racks with chain paths "c" / "c/d/c"
    for i, d in enumerate(t.devices):
        for p in d.parameters:
            add(p, {"device": i, "parameter": p.name})
        if getattr(d, "can_have_chains", False):
            _walk_rack(cs, d, i, [], add)
    return {"track": cs._ref(t), "count": len(out), "parameters": out}


def _walk_rack(cs, rack, top, prefix, add):
    for c, ch in enumerate(rack.chains):
        for k, d in enumerate(ch.devices):
            path = "/".join(str(x) for x in prefix + [c])
            for p in d.parameters:
                add(p, {"device": top, "chain": path, "chain_device": k, "parameter": p.name})
            if getattr(d, "can_have_chains", False):
                _walk_rack(cs, d, top, prefix + [c, k], add)


def cmd_set_automation_points(cs, track, slot, target, points, units="auto", mode="ramp", replace=True):
    """Write breakpoints into a session clip's envelope for one parameter (created if needed).
    points: [{"at": "1.1.1" or beats, "value": v}, ...] in clip-local musical time. mode "ramp": straight lines
    between points; "step": each value holds until the next point. replace clears the points' span first.
    Values are raw, or display units (units="display": dB, Hz, %, ms) converted per point."""
    t, clip, p, env = _envelope(cs, track, slot, target, create=True)
    if env is None:
        raise ToolError("Live gave no envelope for %s (an arrangement clip, or a parameter on another track?)" % p.name)
    pts = sorted(((_beats(cs, x["at"]), _to_raw(cs, p, x["value"], x.get("units", units))) for x in points),
                 key=lambda a: a[0])
    if not pts:
        raise ToolError("no points")
    end = clip.loop_end if clip.looping else clip.end_marker
    for b, _ in pts:
        if b < -1e-9 or b > end + 1e-6:
            raise ToolError("point at beat %g is outside the clip (0..%g)" % (b, end))
    import Live
    if replace:
        env.delete_events_in_range(pts[0][0], pts[-1][0])
    for i, (b, v) in enumerate(pts):
        env.create_event(Live.Envelope.EnvelopeEvent(b, v))
        if mode == "step" and i + 1 < len(pts):
            env.create_event(Live.Envelope.EnvelopeEvent(pts[i + 1][0], v))
    readback = [_read(p, env, b) for b, _ in pts]
    # Two points at one time make a step; just after it Live reads the second, so only that one is compared.
    last_at = {}
    for i, (b, _) in enumerate(pts):
        last_at[round(b, 9)] = i
    bad = [r for i, (r, (b, v)) in enumerate(zip(readback, pts))
           if last_at[round(b, 9)] == i and abs(r["raw"] - v) > max(1e-3, abs(p.max - p.min) * 1e-3)]
    return {"track": cs._ref(t), "parameter": p.name, "points": len(pts), "mode": mode, "readback": readback,
            "mismatches": bad}


def _shape_points(cs, shape, start, end, frm, to, resolution, rate, duty, curve):
    import math
    a, b = _beats(cs, start), _beats(cs, end)
    if b <= a:
        raise ToolError("end must be after start")
    res = float(resolution)
    pts = []
    if shape in ("ramp", "fade", "sweep"):
        if curve == "linear":
            pts = [(a, frm), (b, to)]
        else:
            n = max(2, int((b - a) / res) + 1)
            for i in range(n + 1):
                x = i / float(n)
                y = {"ease": 0.5 - 0.5 * math.cos(math.pi * x), "exp": x * x, "log": 1 - (1 - x) * (1 - x)}.get(curve, x)
                pts.append((a + (b - a) * x, frm + (to - frm) * y))
    elif shape == "hold":
        pts = [(a, frm), (b, frm)]
    elif shape == "pulse":
        period = float(rate)
        x = a
        while x < b - 1e-9:
            on_end = min(x + period * float(duty), b)
            pts += [(x, to), (on_end, to), (on_end, frm), (min(x + period, b), frm)]
            x += period
    elif shape in ("sine", "lfo"):
        period = float(rate)
        n = max(4, int((b - a) / res) + 1)
        for i in range(n + 1):
            x = a + (b - a) * i / float(n)
            pts.append((x, frm + (to - frm) * (0.5 - 0.5 * math.cos(2 * math.pi * (x - a) / period))))
    else:
        raise ToolError("shape: ramp, fade, sweep, hold, pulse, sine")
    return pts


def cmd_set_automation_curve(cs, track, slot, target, shape, start, end, frm, to=None, units="auto",
                             resolution=0.25, rate=1.0, duty=0.5, curve="linear", replace=True):
    """A shaped automation segment in musical time. shape: ramp/sweep/fade (frm -> to; curve linear, ease, exp,
    log), hold (frm), pulse (to for duty of each rate-beat period, else frm), sine (frm..to, period rate beats).
    Display units are converted per point, so a fade in dB is linear in dB."""
    to = frm if to is None else to
    step = shape == "pulse"
    t, clip, p, env = _envelope(cs, track, slot, target, create=True)
    if env is None:
        raise ToolError("Live gave no envelope for %s" % p.name)
    import Live
    # Interpolate in display units when both ends are finite numbers there (a dB fade is then linear in dB, a Hz
    # sweep linear in Hz unless curve shapes it); otherwise (quantized, -inf) interpolate the raw values.
    disp = units == "display" or (units == "auto" and isinstance(frm, str))
    a_num = cs._num(frm) if isinstance(frm, str) else (float(frm) if frm is not None else None)
    b_num = cs._num(to) if isinstance(to, str) else (float(to) if to is not None else None)
    if disp and not p.is_quantized and None not in (a_num, b_num) and float("-inf") not in (a_num, b_num):
        pts = _shape_points(cs, shape, start, end, a_num, b_num, resolution, rate, duty, curve)
        raw = [(b, float(cs._bisect(p, v))) for b, v in pts]
    else:
        ra, rb = _to_raw(cs, p, frm, units), _to_raw(cs, p, to, units)
        raw = _shape_points(cs, shape, start, end, ra, rb, resolution, rate, duty, curve)
    if replace:
        env.delete_events_in_range(raw[0][0], raw[-1][0])
    for b, v in raw:
        env.create_event(Live.Envelope.EnvelopeEvent(b, v))
    probe = [raw[0][0], (raw[0][0] + raw[-1][0]) / 2.0, raw[-1][0] - 1e-3]
    return {"track": cs._ref(t), "parameter": p.name, "shape": shape, "events": len(raw), "stepped": step,
            "samples": [_read(p, env, b) for b in probe]}


def cmd_get_automation(cs, track, slot, target, start=0, end=None, step=1.0):
    """Sample a session clip's envelope in musical time (value_at_time just after each sample point)."""
    t, clip, p, env = _envelope(cs, track, slot, target)
    if env is None:
        return {"track": cs._ref(t), "parameter": p.name, "has_envelope": False}
    a = _beats(cs, start)
    b = _beats(cs, end) if end is not None else (clip.loop_end if clip.looping else clip.end_marker)
    st = float(step)
    out, x = [], a
    while x <= b + 1e-9:
        out.append(_read(p, env, min(x, b - 1e-3)))
        x += st
    return {"track": cs._ref(t), "parameter": p.name, "has_envelope": True, "clip_length": clip.length,
            "looping": bool(clip.looping), "samples": out}


def cmd_delete_automation(cs, track, slot, target=None):
    """Clear one parameter's envelope in a session clip, or every envelope when target is omitted."""
    t, clip = _clip(cs, track, slot)
    if target is None:
        clip.clear_all_envelopes()
        return {"track": cs._ref(t), "cleared": "all"}
    _, p = _target_param(cs, track, target)
    clip.clear_envelope(p)
    return {"track": cs._ref(t), "cleared": p.name, "has_envelope": clip.automation_envelope(p) is not None}


def cmd_copy_automation(cs, track, slot, target, to_track, to_slot, to_target=None, resolution=0.0625):
    """Copy an envelope by sampling it (every `resolution` beats, default a 64th) into another clip/parameter of the
    same raw range. Lossy only below the resolution."""
    t, clip, p, env = _envelope(cs, track, slot, target)
    if env is None:
        raise ToolError("no envelope for %s" % p.name)
    t2, clip2, p2, env2 = _envelope(cs, to_track, to_slot, to_target or target, create=True)
    import Live
    end = min(clip.loop_end if clip.looping else clip.end_marker, clip2.loop_end if clip2.looping else clip2.end_marker)
    env2.delete_events_in_range(0.0, end)
    x, n, prev = 0.0, 0, None
    while x <= end + 1e-9:
        v = float(env.value_at_time(min(x, end - 1e-4) + 1e-4))
        v = min(max(v, p2.min), p2.max)
        if prev is None or abs(v - prev) > 1e-6 or x + float(resolution) > end:
            env2.create_event(Live.Envelope.EnvelopeEvent(x, v))
            n += 1
        prev = v
        x += float(resolution)
    return {"from": [cs._ref(t), slot, p.name], "to": [cs._ref(t2), to_slot, p2.name], "events": n}


def cmd_validate_automation(cs, track, slot, target, expect, units="auto", tolerance=None):
    """Check a session envelope against expected values: expect [{"at": pos, "value": v}]. Also reports the loop
    wrap: the value just before the loop end against the value at the loop start."""
    t, clip, p, env = _envelope(cs, track, slot, target)
    if env is None:
        return {"ok": False, "reason": "no envelope for %s" % p.name}
    tol = float(tolerance) if tolerance is not None else max(1e-3, abs(p.max - p.min) * 0.01)
    rows, ok = [], True
    for e in expect:
        b = _beats(cs, e["at"])
        want = _to_raw(cs, p, e["value"], e.get("units", units))
        got = _read(p, env, b)
        good = abs(got["raw"] - want) <= tol
        ok = ok and good
        rows.append({"at": e["at"], "beat": b, "want_raw": round(want, 6), "want_display": p.str_for_value(want),
                     "got": got, "ok": good})
    ls = clip.loop_start if clip.looping else 0.0
    le = clip.loop_end if clip.looping else clip.end_marker
    wrap = {"value_at_loop_end": _read(p, env, le - 2e-3), "value_at_loop_start": _read(p, env, ls)}
    wrap["jump_raw"] = round(wrap["value_at_loop_start"]["raw"] - wrap["value_at_loop_end"]["raw"], 6)
    return {"ok": ok, "parameter": p.name, "tolerance_raw": tol, "points": rows, "loop_wrap": wrap,
            "automation_state": int(getattr(p, "automation_state", 0))}


# ---------------------------------------------------------------------------------------------- sidechain
def _routing_out(rt):
    return {"name": rt.display_name, "category": getattr(rt, "category", None),
            "attached": getattr(getattr(rt, "attached_object", None), "name", None)}


def _sc_device(cs, track, device, chain=None, chain_device=None):
    t = cs._track(track)
    d = cs._device(t, device)
    if chain not in (None, ""):
        d = cs._device(t, device, chain)[int(chain_device or 0)]
    return t, d


def cmd_inspect_device_sidechain(cs, track, device, chain=None, chain_device=None):
    """Whether a device's sidechain source is reachable through the LOM (routing lists on the device), its current
    source, its choices, and its S/C parameters."""
    t, d = _sc_device(cs, track, device, chain, chain_device)
    sc = [cs._pout(p) for p in d.parameters if p.name.startswith("S/C") or p.original_name.startswith("S/C")]
    out = {"track": cs._ref(t), "device": d.name, "class_name": d.class_name, "sc_parameters": sc,
           "routable": hasattr(d, "available_input_routing_types")}
    if out["routable"]:
        out["source"] = _routing_out(d.input_routing_type)
        out["channel"] = d.input_routing_channel.display_name
        out["choices"] = [_routing_out(r) for r in d.available_input_routing_types]
        out["channels"] = [c.display_name for c in d.available_input_routing_channels]
    return out


def cmd_set_sidechain(cs, track, device, source, channel=None, on=True, chain=None, chain_device=None, params=None,
                      units="display"):
    """Point a device's sidechain at a source (a track ref/name, or a routing choice's exact name), optionally a
    channel ('Pre FX', 'Post FX', 'Post Mixer'), turn S/C on, and set S/C parameters. Refuses a source that is the
    device's own track."""
    t, d = _sc_device(cs, track, device, chain, chain_device)
    if not hasattr(d, "available_input_routing_types"):
        raise ToolError("%s (%s) exposes no sidechain routing through the LOM" % (d.name, d.class_name))
    choices = list(d.available_input_routing_types)
    want = None
    try:
        src = cs._track(source)
        if src == t:
            raise ToolError("a device can't sidechain from its own track")
        want = [r for r in choices if getattr(r, "attached_object", None) == src]
    except ToolError as e:
        if "own track" in str(e):
            raise
        want = [r for r in choices if r.display_name == str(source)]
    except Exception:
        want = [r for r in choices if r.display_name == str(source)]
    if len(want) != 1:
        raise ToolError("sidechain source %r: %d matches; choices are %s" % (source, len(want),
                                                                             [r.display_name for r in choices]))
    d.input_routing_type = want[0]
    if channel is not None:
        chs = [c for c in d.available_input_routing_channels if c.display_name == channel]
        if len(chs) != 1:
            raise ToolError("channel %r not offered: %s" % (channel, [c.display_name for c in d.available_input_routing_channels]))
        d.input_routing_channel = chs[0]
    results = []
    if on is not None:
        p = [x for x in d.parameters if x.name == "S/C On"]
        if p:
            p[0].value = p[0].max if on else p[0].min
    for k, v in (params or {}).items():
        results.append(cs._set_param(cs._param(d, k), v, units))
    return {"device": d.name, "source": _routing_out(d.input_routing_type), "channel": d.input_routing_channel.display_name,
            "sc_on": [cs._pout(x) for x in d.parameters if x.name == "S/C On"], "params": results}


# ---------------------------------------------------------------------------------------------- racks
def cmd_create_effect_rack(cs, track, index=-1, name=None, kind="Audio Effect Rack"):
    """Insert an empty rack (Track.insert_device, Live 12.3+). kind: Audio Effect Rack, Instrument Rack,
    MIDI Effect Rack, Drum Rack."""
    t = cs._track(track)
    d = t.insert_device(kind) if index is None or int(index) < 0 else t.insert_device(kind, int(index))
    if name:
        d.name = name
    return {"track": cs._ref(t), "rack": d.name, "class_name": d.class_name,
            "index": list(t.devices).index(d), "chains": len(d.chains)}


def _rack(cs, track, device, chain=None, chain_device=None):
    t, d = _sc_device(cs, track, device, chain, chain_device)
    if not getattr(d, "can_have_chains", False):
        raise ToolError("%s is not a rack" % d.name)
    return t, d


def cmd_add_rack_chain(cs, track, device, name=None, index=-1, chain=None, chain_device=None):
    """Add a chain to a rack (RackDevice.insert_chain, Live 12.3+)."""
    t, r = _rack(cs, track, device, chain, chain_device)
    ch = r.insert_chain() if index is None or int(index) < 0 else r.insert_chain(int(index))
    if ch is None:
        ch = list(r.chains)[-1 if index is None or int(index) < 0 else int(index)]
    if name:
        ch.name = name
    return {"rack": r.name, "chains": [c.name for c in r.chains]}


def cmd_insert_device_in_chain(cs, track, device, chain_index, name, index=-1, chain=None, chain_device=None):
    """Insert a native device into a rack chain by its exact browser name (Chain.insert_device)."""
    t, r = _rack(cs, track, device, chain, chain_device)
    chains = list(r.chains)
    if not 0 <= int(chain_index) < len(chains):
        raise ToolError("chain %s out of range (%d chains)" % (chain_index, len(chains)))
    ch = chains[int(chain_index)]
    d = ch.insert_device(name) if index is None or int(index) < 0 else ch.insert_device(name, int(index))
    return {"rack": r.name, "chain": ch.name, "inserted": d.name, "devices": [x.name for x in ch.devices]}


def cmd_set_chain_mixer(cs, track, device, chain_index, volume_db=None, pan=None, active=None, chain=None,
                        chain_device=None):
    """A rack chain's volume (dB as displayed), pan (-50..50) and activator."""
    t, r = _rack(cs, track, device, chain, chain_device)
    ch = list(r.chains)[int(chain_index)]
    m = ch.mixer_device
    res = {}
    if volume_db is not None:
        res["volume"] = cs._set_param(m.volume, volume_db, "display")["after"]["display"]
    if pan is not None:
        res["pan"] = cs._set_param(m.panning, pan, "display")["after"]["display"]
    if active is not None:
        m.chain_activator.value = m.chain_activator.max if active else m.chain_activator.min
        res["active"] = bool(m.chain_activator.value)
    return {"rack": r.name, "chain": ch.name, "now": res}


def cmd_set_rack_macros(cs, track, device, visible=None, values=None, units="auto", chain=None, chain_device=None):
    """Show `visible` macros (add_macro/remove_macro) and set macro values {"Macro 1": v}. Mapping a macro to a
    parameter is not in the LOM (see map_macro: a rack preset written with the mapping)."""
    t, r = _rack(cs, track, device, chain, chain_device)
    if visible is not None and hasattr(r, "visible_macro_count"):
        guard = 0
        while r.visible_macro_count < int(visible) and guard < 16:
            r.add_macro(); guard += 1
        while r.visible_macro_count > int(visible) and guard < 32:
            r.remove_macro(); guard += 1
    res = [cs._set_param(cs._param(r, k), v, units) for k, v in (values or {}).items()]
    return {"rack": r.name, "visible_macros": getattr(r, "visible_macro_count", None),
            "has_macro_mappings": getattr(r, "has_macro_mappings", None), "results": res}


# ---------------------------------------------------------------------------------------------- clips
def _any_clip(cs, track, slot=None, arrangement_index=None):
    t = cs._track(track)
    if arrangement_index is not None:
        cl = list(t.arrangement_clips)
        if not 0 <= int(arrangement_index) < len(cl):
            raise ToolError("arrangement clip %s out of range (%d)" % (arrangement_index, len(cl)))
        return t, cl[int(arrangement_index)]
    return _clip(cs, track, slot)


def _clip_out(c):
    out = {"name": c.name, "is_audio": bool(c.is_audio_clip), "length": c.length, "looping": bool(c.looping),
           "start_marker": c.start_marker, "end_marker": c.end_marker, "loop_start": c.loop_start,
           "loop_end": c.loop_end}
    if getattr(c, "is_arrangement_clip", False):
        out["start_time"] = c.start_time
        out["end_time"] = c.end_time
    if c.is_audio_clip:
        out.update({"pitch_coarse": c.pitch_coarse, "pitch_fine": c.pitch_fine, "gain": c.gain,
                    "gain_display": c.gain_display_string, "warping": bool(c.warping), "warp_mode": c.warp_mode,
                    "available_warp_modes": list(c.available_warp_modes), "file_path": c.file_path,
                    "sample_rate": getattr(c, "sample_rate", None)})
        try:
            out["warp_markers"] = [{"beat": w.beat_time, "seconds": w.sample_time} for w in c.warp_markers]
        except Exception:
            pass
    return out


def cmd_get_clip(cs, track, slot=None, arrangement_index=None):
    t, c = _any_clip(cs, track, slot, arrangement_index)
    return dict(_clip_out(c), track=cs._ref(t))


def cmd_set_clip(cs, track, slot=None, arrangement_index=None, name=None, pitch_coarse=None, pitch_fine=None,
                 gain=None, warping=None, warp_mode=None, looping=None, loop_start=None, loop_end=None,
                 start_marker=None, end_marker=None):
    """Clip properties in musical time (positions as beats or 'bar.beat.sixteenth'). warp_mode: 0 beats, 1 tones,
    2 texture, 3 re-pitch, 4 complex, 6 complex pro. Reads everything back."""
    t, c = _any_clip(cs, track, slot, arrangement_index)
    if name is not None:
        c.name = name
    if c.is_audio_clip:
        if warping is not None:
            c.warping = bool(warping)
        if warp_mode is not None:
            if int(warp_mode) not in list(c.available_warp_modes):
                raise ToolError("warp mode %s not available: %s" % (warp_mode, list(c.available_warp_modes)))
            c.warp_mode = int(warp_mode)
        if pitch_coarse is not None:
            c.pitch_coarse = int(pitch_coarse)
        if pitch_fine is not None:
            c.pitch_fine = float(pitch_fine)
        if gain is not None:
            c.gain = float(gain)
    # Live ignores start_marker writes on an unlooped clip (measured 2026-11-10), so markers are written while the
    # clip loops, and looping is switched off last.
    was = bool(c.looping)
    if (start_marker is not None or end_marker is not None) and not was:
        c.looping = True
    if loop_end is not None:
        c.loop_end = _beats(cs, loop_end)
    if loop_start is not None:
        c.loop_start = _beats(cs, loop_start)
    if end_marker is not None:
        c.end_marker = _beats(cs, end_marker)
    if start_marker is not None:
        c.start_marker = _beats(cs, start_marker)
    if looping is not None:
        c.looping = bool(looping)
    elif c.looping != was:
        c.looping = was
    return dict(_clip_out(c), track=cs._ref(t))


def cmd_warp_marker(cs, track, action, beat, slot=None, arrangement_index=None, seconds=None, delta=None):
    """action add (beat + seconds), move (beat, delta beats) or remove (beat) on an audio clip."""
    import Live
    t, c = _any_clip(cs, track, slot, arrangement_index)
    if not c.is_audio_clip:
        raise ToolError("warp markers need an audio clip")
    b = _beats(cs, beat)
    if action == "add":
        c.add_warp_marker(Live.Clip.WarpMarker(sample_time=float(seconds), beat_time=b))
    elif action == "move":
        c.move_warp_marker(b, float(delta))
    elif action == "remove":
        c.remove_warp_marker(b)
    else:
        raise ToolError("action: add, move, remove")
    return dict(_clip_out(c), track=cs._ref(t))


def cmd_set_song_time(cs, tempo=None, numerator=None, denominator=None, loop=None, loop_start=None, loop_length=None,
                      position=None):
    """Tempo, time signature (denominator 1/2/4/8/16) and the arrangement loop brace, in musical time."""
    s = cs._song
    if tempo is not None:
        s.tempo = float(tempo)
    if numerator is not None:
        s.signature_numerator = int(numerator)
    if denominator is not None:
        s.signature_denominator = int(denominator)
    if loop_start is not None:
        s.loop_start = _beats(cs, loop_start)
    if loop_length is not None:
        s.loop_length = float(loop_length) if not isinstance(loop_length, str) else _beats(cs, loop_length)
    if loop is not None:
        s.loop = bool(loop)
    if position is not None:
        # Playback starts from the start marker (Song.start_time), not the playhead: setting only
        # current_song_time while stopped still started at beat 0 (measured 2026-11-10). Set both.
        b = _beats(cs, position)
        s.start_time = b
        s.current_song_time = b
    return {"tempo": s.tempo, "position": s.current_song_time, "start_marker": s.start_time, "signature": "%d/%d" % (s.signature_numerator, s.signature_denominator),
            "loop": bool(s.loop), "loop_start": s.loop_start, "loop_length": s.loop_length,
            "note": "loop changes apply on Live's next tick: read back with set_song_time() after a moment"}


# ---------------------------------------------------------------------------------------------- in-Live capture
_CAPTURE = {}


def cmd_capture_start(cs, tracks, seconds=16.0, params=None):
    """Sample output meters (dBFS = 76*raw-70) and optional parameters inside Live on every UI tick (about 10 Hz),
    stamped with song time, for `seconds`. params: [{"track": ref, "target": {...}}]. Read with capture_result."""
    ts = [cs._track(r) for r in tracks]
    ps = [(x, _target_param(cs, x["track"], x["target"])[1]) for x in (params or [])]
    cap = {"rows": [], "done": False, "until": None}
    _CAPTURE["current"] = cap
    import time as _t
    cap["until"] = _t.time() + float(seconds)

    def tick():
        if _CAPTURE.get("current") is not cap:
            return
        row = {"t": round(float(cs._song.current_song_time), 4), "playing": bool(cs._song.is_playing)}
        for t in ts:
            lvl = float(t.output_meter_level)
            row[cs._ref(t)] = round(76.0 * lvl - 70.0, 2) if lvl > 0 else None
        for x, p in ps:
            row["%s:%s" % (x["track"], p.name)] = round(float(p.value), 5)
        cap["rows"].append(row)
        if _t.time() < cap["until"]:
            cs.schedule_message(1, tick)
        else:
            cap["done"] = True

    cs.schedule_message(1, tick)
    return {"started": True, "seconds": seconds}


def cmd_capture_result(cs):
    cap = _CAPTURE.get("current")
    if cap is None:
        raise ToolError("no capture started")
    return {"done": cap["done"], "count": len(cap["rows"]), "rows": cap["rows"] if cap["done"] else []}


# ---------------------------------------------------------------------------------------------- arrangement
def cmd_duplicate_to_arrangement(cs, track, slot, at):
    """Copy a session clip into the Arrangement at a musical position (Track.duplicate_clip_to_arrangement).
    Reports whether the copy kept its clip envelopes (the repos disagree; measure it here)."""
    t, clip = _clip(cs, track, slot)
    before = len(list(t.arrangement_clips))
    t.duplicate_clip_to_arrangement(clip, _beats(cs, at))
    cl = list(t.arrangement_clips)
    new = [c for c in cl if abs(c.start_time - _beats(cs, at)) < 1e-6]
    c = new[-1] if new else cl[-1]
    return {"track": cs._ref(t), "arrangement_clips": len(cl), "added": len(cl) - before,
            "start": c.start_time, "end": c.end_time, "source_had_envelopes": bool(clip.has_envelopes),
            "copy_has_envelopes": bool(getattr(c, "has_envelopes", False)),
            "index": cl.index(c)}


def cmd_delete_arrangement_clip(cs, track, index=None, at=None):
    """Delete one arrangement clip, found by its start `at` (a song position) or its `index`. Disposable sets only."""
    cs._require_scratch()
    t, c = _aclip_ref(cs, track, index, at)
    gone = {"name": c.name, "start": c.start_time, "end": c.end_time}
    t.delete_clip(c)
    return {"track": cs._ref(t), "deleted": gone, "arrangement_clips": len(list(t.arrangement_clips))}


_REC = {}
SETTLE_BEATS = 0.5   # wait this long after recording starts rolling before the gesture (see record_arrangement_automation)


def _interp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if a <= x <= b:
            if b - a < 1e-9:
                return vb
            return va + (vb - va) * (x - a) / (b - a)
    return pts[-1][1]


def cmd_record_arrangement_automation(cs, track, target, points, units="auto", preroll_bars=1):
    """Record automation into the Arrangement in real time: Automation Arm on, Arrangement Record on, play from a bar
    before the first point, write the parameter every UI tick (~10 Hz) inside a begin/end gesture, then stop and
    restore the transport state. points: [{"at": pos, "value": v}] in song time (bars from the song start); straight
    lines between points. Armed tracks are disarmed for the pass so nothing else records. Asynchronous: poll
    record_arrangement_status. The LOM can't draw arrangement automation, so this is the supported route."""
    t, p = _target_param(cs, track, target)
    pts = sorted(((_beats(cs, x["at"]), _to_raw(cs, p, x["value"], x.get("units", units))) for x in points),
                 key=lambda a: a[0])
    if len(pts) < 2:
        raise ToolError("give at least two points")
    s = cs._song
    if s.is_playing:
        raise ToolError("stop playback first")
    state = {"loop": s.loop, "time": s.current_song_time, "aarm": s.session_automation_record,
             "armed": [x for x in s.tracks if getattr(x, "can_be_armed", False) and x.arm],
             "punch_in": s.punch_in, "punch_out": s.punch_out}
    for x in state["armed"]:
        x.arm = False
    # A MIDI controller makes Live arm the selected MIDI track implicitly (Track.implicit_arm), which `arm` doesn't
    # show; that pass then records silence over the track's clips (measured 2026-11-10: it overwrote an 8-bar clip).
    # Select the Main track for the pass so nothing is implicitly armed.
    state["selected"] = s.view.selected_track
    s.view.selected_track = s.master_track
    implicit = [x.name for x in s.tracks if getattr(x, "implicit_arm", False)]
    if implicit:
        raise ToolError("tracks still implicitly armed: %s" % implicit)
    start = max(0.0, pts[0][0] - float(preroll_bars) * _beats_per_bar(cs))
    rec = {"phase": "arming", "written": 0, "done": False, "error": None, "start": start, "end": pts[-1][0],
           "parameter": p.name, "first_value": None}
    _REC["current"] = rec
    p.value = pts[0][1]
    s.stop_all_clips()
    if s.back_to_arranger:
        s.back_to_arranger = False        # "Back to Arrangement": tracks follow the Arrangement again
    s.loop = False
    s.punch_in = False
    s.punch_out = False
    s.session_automation_record = True
    s.current_song_time = start

    def finish(err=None):
        try:
            if rec.get("gesture"):
                p.end_gesture()
        except Exception:
            pass
        s.record_mode = False
        s.stop_playing()
        s.session_automation_record = state["aarm"]
        s.loop = state["loop"]
        s.punch_in, s.punch_out = state["punch_in"], state["punch_out"]
        for x in state["armed"]:
            x.arm = True
        try:
            s.view.selected_track = state["selected"]
        except Exception:
            pass
        rec["error"] = err
        rec["done"] = True
        rec["phase"] = "done"

    def tick():
        if _REC.get("current") is not rec or rec["done"]:
            return
        try:
            if rec["phase"] == "arming":
                live = [x.name for x in s.tracks if getattr(x, "can_be_armed", False)
                        and (x.arm or getattr(x, "implicit_arm", False))]
                if live:                      # never record over clips: refuse instead
                    finish("tracks still armed, refusing to record: %s" % live)
                    return
                s.record_mode = True          # starts playback ("Start Playback with Record")
                rec["phase"] = "rolling"
            else:
                now = float(s.current_song_time)
                rec["record_mode_seen"] = rec.get("record_mode_seen", False) or bool(s.record_mode)
                rec["playing_seen"] = rec.get("playing_seen", False) or bool(s.is_playing)
                # Begin the gesture only once Live is really recording and rolling: a gesture begun in the tick
                # record_mode was switched on is not recorded at all (measured 2026-11-10, a pass from bar 1).
                if not rec.get("rolling_since") and s.record_mode and s.is_playing:
                    rec["rolling_since"] = now
                settle = rec.get("rolling_since") is not None and now >= rec["rolling_since"] + float(SETTLE_BEATS)
                if now >= pts[0][0] and not rec.get("gesture") and settle:
                    p.begin_gesture()
                    rec["gesture"] = True
                if rec.get("gesture"):
                    v = _interp(pts, now)
                    p.value = min(max(v, p.min), p.max)
                    rec["written"] += 1
                if now >= pts[-1][0]:
                    p.value = pts[-1][1]
                    finish()
                    return
            cs.schedule_message(1, tick)
        except Exception as e:
            finish("%s: %s" % (type(e).__name__, e))

    cs.schedule_message(1, tick)
    return {"started": True, "parameter": p.name, "from_beat": start, "to_beat": pts[-1][0],
            "seconds": (pts[-1][0] - start) * 60.0 / s.tempo}


def cmd_record_arrangement_status(cs):
    rec = _REC.get("current")
    if rec is None:
        raise ToolError("no recording started")
    return {k: v for k, v in rec.items() if k != "gesture"}


def cmd_param_state(cs, track, target):
    """A parameter's value and automation state (0 none, 1 playing, 2 overridden: re-enable to follow again)."""
    t, p = _target_param(cs, track, target)
    return {"parameter": p.name, "value": p.value, "display": p.str_for_value(p.value),
            "automation_state": int(getattr(p, "automation_state", 0))}


def cmd_re_enable_automation(cs, track=None, target=None):
    if target is not None:
        t, p = _target_param(cs, track, target)
        p.re_enable_automation()
        return {"parameter": p.name, "automation_state": int(p.automation_state)}
    cs._song.re_enable_automation()
    return {"song": True}


def cmd_set_arm(cs, track, arm):
    """Arm or disarm a track for recording; reports explicit and implicit (controller-selected) arm."""
    t = cs._track(track)
    if not getattr(t, "can_be_armed", False):
        raise ToolError("%s can't be armed" % t.name)
    t.arm = bool(arm)
    return {"track": cs._ref(t), "arm": bool(t.arm), "implicit_arm": bool(getattr(t, "implicit_arm", False))}


def cmd_back_to_arrangement(cs):
    """Press Back to Arrangement: every track follows the Arrangement (and its automation) again. Needed after
    stopping session clips, which leaves tracks detached from the Arrangement."""
    s = cs._song
    was = bool(s.back_to_arranger)
    if was:
        s.back_to_arranger = False
    return {"was_detached": was, "note": "applies on Live's next tick"}


# ---------------------------------------------------------------------------------------------- recording
_RECA = {}


def cmd_record_track_audio(cs, dst, source, slot=0, bars=2, channel=None, monitoring="off"):
    """Record a track's output into a session clip on an audio track: input = the source track (or "Resampling"
    for the Main), monitoring off (so the source isn't heard twice), arm, launch the slot recording, and stop it
    after exactly `bars` bars on Live's clock. Asynchronous: poll record_track_audio_status. The source must play
    (fire its clip or play the Arrangement) during the pass."""
    t = cs._track(dst)
    if t.has_midi_input:
        raise ToolError("%s is a MIDI track: record audio onto an audio track" % t.name)
    slot = int(slot)
    if slot < 0:
        raise ToolError("slot must be 0 or more, got %s" % slot)
    have = len(list(t.clip_slots))
    added = max(0, slot + 1 - have)
    if added > 16:
        raise ToolError("slot %s is far past %s's %d Session slots (last is %d)" % (slot, t.name, have, have - 1))
    for _ in range(added):              # just past the last scene: add empty scenes at the end, as Live's
        cs._song.create_scene(-1)       # Session view does when you record below the last one
    cslot = list(t.clip_slots)[slot]
    if cslot.has_clip:
        raise ToolError("slot %s of %s already holds a clip" % (slot, t.name))
    choices = list(t.available_input_routing_types)
    try:
        src = cs._track(source)
        want = [r for r in choices if getattr(r, "attached_object", None) == src]
    except Exception:
        want = [r for r in choices if r.display_name == str(source)]
    if len(want) != 1:
        raise ToolError("input %r: %d matches; choices %s" % (source, len(want), [r.display_name for r in choices]))
    t.input_routing_type = want[0]
    rec = {"phase": "routing", "done": False, "error": None}
    _RECA["current"] = rec
    length = float(bars) * _beats_per_bar(cs)

    def tick():
        if _RECA.get("current") is not rec or rec["done"]:
            return
        try:
            if rec["phase"] == "routing":       # routing applies on the next tick
                if channel is not None:
                    chs = [c for c in t.available_input_routing_channels if c.display_name == channel]
                    if len(chs) != 1:
                        raise ToolError("channel %r not offered: %s" % (channel, [c.display_name for c in t.available_input_routing_channels]))
                    t.input_routing_channel = chs[0]
                t.current_monitoring_state = {"in": 0, "auto": 1, "off": 2}[monitoring]
                t.arm = True
                rec["input"] = t.input_routing_type.display_name
                rec["channel"] = t.input_routing_channel.display_name
                rec["phase"] = "launch"
            elif rec["phase"] == "launch":
                try:
                    cslot.fire(record_length=length)
                    rec["method"] = "fire(record_length)"
                except TypeError:
                    cslot.fire()
                    rec["method"] = "fire() + timed stop"
                rec["phase"] = "recording"
            elif rec["phase"] == "recording":
                c = cslot.clip
                if c is not None and c.is_recording:
                    rec["started"] = True
                if rec.get("started") and c is not None and not c.is_recording:
                    t.arm = False
                    rec.update(phase="done", done=True, clip_length=c.length, file=c.file_path)
                    fp = c.file_path or ""
                    if "Temp Project" in fp or "/Live Recordings/" in fp:
                        rec["warning"] = ("recorded outside this Set's project (%s): the Set isn't saved inside a Live "
                                          "project folder yet. Save it (File > Save Live Set As, or Collect All and "
                                          "Save) so the take moves with it" % fp)
                    return
                if rec.get("method", "").startswith("fire()") and c is not None and c.is_recording \
                        and c.length >= length:
                    cslot.fire()                 # a second launch ends the recording
            cs.schedule_message(1, tick)
        except Exception as e:
            t.arm = False
            rec.update(phase="done", done=True, error="%s: %s" % (type(e).__name__, e))

    cs.schedule_message(1, tick)
    return {"started": True, "dst": cs._ref(t), "slot": slot, "scenes_added": added, "bars": bars, "beats": length}


def cmd_record_track_audio_status(cs):
    rec = _RECA.get("current")
    if rec is None:
        raise ToolError("no recording started")
    return dict(rec)


def cmd_create_audio_clip(cs, track, path, slot=None, at=None):
    """Load an audio file as a clip: into a session slot (ClipSlot.create_audio_clip) or into the Arrangement at a
    musical position (Track.create_audio_clip). Audio tracks only; the path must be absolute. In the Arrangement it
    pastes over whatever is there (it splits or trims existing clips)."""
    import os
    t = cs._track(track)
    if t.has_midi_input:
        raise ToolError("%s is a MIDI track" % t.name)
    if not os.path.isabs(path) or not os.path.exists(path):
        raise ToolError("not an existing absolute path: %s" % path)
    if slot is not None:
        cslot = list(t.clip_slots)[int(slot)]
        if cslot.has_clip:
            raise ToolError("slot %s already holds a clip" % slot)
        cslot.create_audio_clip(path)
        return dict(_clip_out(cslot.clip), track=cs._ref(t), slot=int(slot))
    if at is None:
        raise ToolError("give slot or at")
    c = t.create_audio_clip(path, _beats(cs, at))
    return dict(_clip_out(c), track=cs._ref(t))


# ---------------------------------------------------------------------------------------------- arrangement editing
# Measured on 12.4.16: an unlooped arrangement clip's length follows its markers (end_time = start_time + end_marker -
# start_marker); start_marker moves the content, not the clip; there is no API to move or resize a clip in place, so a
# move is a verified copy (duplicate_clip_to_arrangement, which pastes over whatever is there) and a delete. Moves go
# through a temporary spot past the track's last clip so a short shift never pastes over its own source.
def _aclips(t):
    return list(t.arrangement_clips)


def _aclip_at(t, start, tol=1e-6):
    hits = [c for c in _aclips(t) if abs(c.start_time - start) < tol]
    if not hits:
        raise ToolError("no arrangement clip starting at beat %g on %s" % (start, t.name))
    return hits[-1]


def _temp_pos(t):
    ends = [c.end_time for c in _aclips(t)]
    bpb = 4.0
    return (max(ends) if ends else 0.0) + 16 * bpb


def _same(a, b):
    return abs(a.length - b.length) < 1e-6 and a.name == b.name and a.is_audio_clip == b.is_audio_clip


def _aclip_ref(cs, track, index=None, at=None):
    t = cs._track(track)
    if at is not None:
        return t, _aclip_at(t, _beats(cs, at))
    cl = _aclips(t)
    if index is None or not 0 <= int(index) < len(cl):
        raise ToolError("arrangement clip index %s out of range (%d clips)" % (index, len(cl)))
    return t, cl[int(index)]


def cmd_list_arrangement_clips(cs, track):
    t = cs._track(track)
    return {"track": cs._ref(t), "clips": [{"index": i, "name": c.name, "start": c.start_time, "end": c.end_time,
                                             "looping": bool(c.looping), "audio": bool(c.is_audio_clip)}
                                            for i, c in enumerate(_aclips(t))]}


def cmd_copy_arrangement_clip(cs, track, to, index=None, at=None, to_track=None):
    """Copy an arrangement clip to a musical position (and optionally another track of the same kind). The copy
    pastes over whatever is at the destination."""
    t, c = _aclip_ref(cs, track, index, at)
    dt = cs._track(to_track) if to_track is not None else t
    if dt.has_midi_input != t.has_midi_input:
        raise ToolError("copy MIDI clips to MIDI tracks and audio clips to audio tracks")
    new = dt.duplicate_clip_to_arrangement(c, _beats(cs, to))
    return {"track": cs._ref(dt), "start": new.start_time, "end": new.end_time, "name": new.name}


def cmd_move_arrangement_clip(cs, track, to, index=None, at=None, to_track=None):
    """Move an arrangement clip: copy to a temporary spot, verify, delete the original, copy to the destination,
    verify, delete the temporary copy. Content (markers, loop, envelopes the clip carries) moves with it."""
    t, c = _aclip_ref(cs, track, index, at)
    dt = cs._track(to_track) if to_track is not None else t
    if dt.has_midi_input != t.has_midi_input:
        raise ToolError("move MIDI clips to MIDI tracks and audio clips to audio tracks")
    dest = _beats(cs, to)
    tmp_pos = max(_temp_pos(t), _temp_pos(dt))
    tmp = dt.duplicate_clip_to_arrangement(c, tmp_pos)
    if not _same(tmp, c):
        dt.delete_clip(tmp)
        raise ToolError("temporary copy didn't match the source; nothing moved")
    t.delete_clip(c)
    tmp = _aclip_at(dt, tmp_pos)
    new = dt.duplicate_clip_to_arrangement(tmp, dest)
    ok = _same(new, tmp)
    dt.delete_clip(_aclip_at(dt, tmp_pos))
    if not ok:
        raise ToolError("final copy didn't match; the clip is at beat %g, check it" % dest)
    new = _aclip_at(dt, dest)
    return {"track": cs._ref(dt), "start": new.start_time, "end": new.end_time, "name": new.name}


def cmd_trim_arrangement_clip(cs, track, index=None, at=None, start=None, end=None):
    """Trim an arrangement clip to [start, end) in song time, keeping its content in place (the clip is unlooped).
    Trimming the head shifts the start marker and moves the clip, so the audio/MIDI stays where it was."""
    t, c = _aclip_ref(cs, track, index, at)
    s0, e0 = c.start_time, c.end_time
    ns = _beats(cs, start) if start is not None else s0
    ne = _beats(cs, end) if end is not None else e0
    if not s0 - 1e-9 <= ns < ne <= e0 + 1e-9:
        raise ToolError("trim must stay inside the clip (%g..%g): got %g..%g" % (s0, e0, ns, ne))
    if c.looping:
        c.looping = False
    # For an unlooped clip, the LOM's clip start/end are loop_start/loop_end (the markers alone didn't carry into a
    # copy: a head-trimmed copy came out at full length, measured 2026-11-10). Set both pairs, end first.
    base = c.loop_start
    new_end = base + (ne - s0)
    c.loop_end = new_end
    c.end_marker = new_end
    if ns > s0 + 1e-9:
        new_start = base + (ns - s0)
        c.loop_start = new_start
        c.start_marker = new_start
        moved = cmd_move_arrangement_clip(cs, track, ns, at=s0)
        c = _aclip_at(t, ns)
    return {"track": cs._ref(t), "start": c.start_time, "end": c.end_time, "start_marker": c.start_marker,
            "end_marker": c.end_marker}


def cmd_split_arrangement_clip(cs, track, split_at, index=None, at=None):
    """Split an arrangement clip at a song position into two clips that play exactly as before."""
    t, c = _aclip_ref(cs, track, index, at)
    s0, e0 = c.start_time, c.end_time
    x = _beats(cs, split_at)
    if not s0 + 1e-9 < x < e0 - 1e-9:
        raise ToolError("split point %g is not inside the clip (%g..%g)" % (x, s0, e0))
    tmp_pos = _temp_pos(t)
    t.duplicate_clip_to_arrangement(c, tmp_pos)          # second half, prepared away from the source
    a = cmd_trim_arrangement_clip(cs, track, at=s0, end=x)
    b = cmd_trim_arrangement_clip(cs, track, at=tmp_pos, start=tmp_pos + (x - s0))
    moved = cmd_move_arrangement_clip(cs, track, x, at=tmp_pos + (x - s0))
    return {"track": cs._ref(t), "first": [a["start"], a["end"]], "second": [moved["start"], moved["end"]]}


def cmd_create_arrangement_midi_clip(cs, track, at, length, notes=None, name=None):
    """An empty or filled MIDI clip directly in the Arrangement (Track.create_midi_clip). notes: [[pitch, start,
    length, velocity], ...] in clip beats."""
    import Live
    t = cs._track(track)
    if not t.has_midi_input:
        raise ToolError("%s is not a MIDI track" % t.name)
    c = t.create_midi_clip(_beats(cs, at), float(length) if not isinstance(length, str) else _beats(cs, length))
    if name:
        c.name = name
    if notes:
        c.add_new_notes(tuple(Live.Clip.MidiNoteSpecification(pitch=int(p), start_time=float(s), duration=float(d),
                                                              velocity=float(v), mute=False) for p, s, d, v in notes))
    return {"track": cs._ref(t), "start": c.start_time, "end": c.end_time, "name": c.name}


# ---------------------------------------------------------------------------------------------- view (no edits)
def cmd_show_clip(cs, track, slot=0):
    """Select a session clip and show it in Live's Clip View (changes only what's on screen)."""
    t = cs._track(track)
    cslot = list(t.clip_slots)[int(slot)]
    cs._song.view.selected_track = t
    cs._song.view.highlighted_clip_slot = cslot
    cs.application().view.show_view("Detail/Clip")
    return {"track": cs._ref(t), "slot": int(slot), "view": "Detail/Clip"}


def cmd_show_view(cs, name):
    """Show one of Live's main views: "Arranger" or "Session" (changes only what's on screen)."""
    if name not in ("Arranger", "Session"):
        raise ToolError("name: Arranger or Session")
    cs.application().view.show_view(name)
    return {"view": name}


def cmd_show_devices(cs, track):
    """Select a track and show its devices in Live's Device View (changes only what's on screen)."""
    t = cs._track(track)
    cs._song.view.selected_track = t
    cs.application().view.show_view("Detail/DeviceChain")
    return {"track": cs._ref(t), "view": "Detail/DeviceChain"}


# ------------------------------------------------------------------------------------- parameters by name
_KIND = {1: "instrument", 2: "audio_effect", 4: "midi_effect"}


def _walk_devices(devs, top=None, prefix=()):
    """Every device on a track, racks included: (top device index, chain path or None, chain_device or None, device).
    The address is what set_device_parameter takes (device, chain, chain_device)."""
    for j, d in enumerate(devs):
        if top is None:
            here = (j, None, None)
        else:
            here = (top, "/".join(str(x) for x in prefix), j)
        yield here + (d,)
        if getattr(d, "can_have_chains", False):
            for c, ch in enumerate(d.chains):
                path = (prefix + (j, c)) if top is not None else (c,)
                for sub in _walk_devices(list(ch.devices), here[0], path):
                    yield sub


def _find_params(cs, t, name):
    key = str(name).strip().lower()
    hits = []
    for top, chain, cd, d in _walk_devices(list(t.devices)):
        for i, p in enumerate(d.parameters):
            if p.name.lower() == key or p.original_name.lower() == key:
                hits.append({"device": top, "chain": chain, "chain_device": cd, "device_name": d.name,
                             "kind": _KIND.get(int(getattr(d, "type", 0) or 0), "other"), "parameter": p.name,
                             "index": i, "value": p.value, "min": p.min, "max": p.max,
                             "display": p.str_for_value(p.value), "quantized": bool(p.is_quantized), "_p": p})
    return hits


def _public(h):
    return {k: v for k, v in h.items() if k != "_p"}


def cmd_find_parameter(cs, track, name):
    """Every parameter called `name` (its shown or original name, any case) on any device of a track, racks and
    nested racks included. Each match gives its address (device, chain, chain_device, as set_device_parameter takes
    them), device name and kind, raw value, range and display."""
    t = cs._track(track)
    return {"track": cs._ref(t), "name": name, "matches": [_public(h) for h in _find_params(cs, t, name)]}


def cmd_set_parameter_by_name(cs, track, name, value, units="auto", prefer=None, device_name=None):
    """Set the one parameter called `name` on a track, wherever it is (racks included). When several devices have
    it, narrow with prefer ("instrument", "audio_effect", "midi_effect") and/or device_name; if it is still
    ambiguous nothing is written and every match is listed."""
    t = cs._track(track)
    hits = _find_params(cs, t, name)
    if not hits:
        raise ToolError("no parameter %r on any device of %s" % (name, t.name))
    pool = hits
    if device_name:
        pool = [h for h in pool if h["device_name"].lower() == str(device_name).lower()]
    if prefer and len(pool) > 1:
        pool = [h for h in pool if h["kind"] == prefer] or pool
    if len(pool) != 1:
        raise ToolError("%r on %s: %d matches after narrowing; nothing written. Matches: %s"
                        % (name, t.name, len(pool), [_public(h) for h in (pool or hits)]))
    h = pool[0]
    r = cs._set_param(h["_p"], value, units)
    r.update({"track": cs._ref(t), "at": _public(h)})
    return r


# ------------------------------------------------------------------------------------- arrangement range and multi-track recording
def cmd_cut_arrangement_range(cs, tracks, start, end):
    """Remove everything in [start, end) song time from one or more tracks' Arrangement: clips that cross an edge
    are split there (split_arrangement_clip, plays as before), then every clip inside the range is deleted. Nothing
    moves: the range is left empty. Disposable sets only."""
    cs._require_scratch()
    s, e = _beats(cs, start), _beats(cs, end)
    if not s < e:
        raise ToolError("cut range is empty: start %g must be before end %g" % (s, e))
    eps = 1e-6
    out = []
    for ref in (tracks if isinstance(tracks, (list, tuple)) else [tracks]):
        t = cs._track(ref)
        splits = 0
        for x in (s, e):
            for c in [c for c in _aclips(t) if c.start_time + eps < x < c.end_time - eps]:
                cmd_split_arrangement_clip(cs, ref, x, at=c.start_time)
                splits += 1
        inside = [c for c in _aclips(t) if c.start_time >= s - eps and c.end_time <= e + eps]
        gone = [[c.start_time, c.end_time] for c in inside]
        for c in inside:
            t.delete_clip(c)
        left = [[c.start_time, c.end_time] for c in _aclips(t) if c.start_time < e - eps and c.end_time > s + eps]
        if left:
            raise ToolError("%s: clips still overlap the cut after it ran: %s" % (t.name, left))
        out.append({"track": cs._ref(t), "splits": splits, "deleted": gone})
    return {"start": s, "end": e, "tracks": out}


def cmd_record_tracks_audio(cs, takes, bars=2):
    """Several record_track_audio takes in ONE pass: takes = [{"dst", "source", "slot"?, "channel"?}, ...], each dst
    a different audio track. All are routed and armed first, then every slot is launched in the same tick, so they
    start together on Live's launch quantization and each stops after exactly `bars` bars. Asynchronous: poll
    record_tracks_audio_status. Set the playhead first and don't press play (the launch starts the transport)."""
    if not takes:
        raise ToolError("takes is empty")
    length = float(bars) * _beats_per_bar(cs)
    prep, seen = [], set()
    for k in takes:
        t = cs._track(k["dst"])
        if t.has_midi_input:
            raise ToolError("%s is a MIDI track: record audio onto an audio track" % t.name)
        if t in seen:
            raise ToolError("%s is listed twice: one take per destination track" % t.name)
        seen.add(t)
        slot = int(k.get("slot") or 0)
        if slot < 0:
            raise ToolError("slot must be 0 or more, got %s" % slot)
        have = len(list(t.clip_slots))
        if slot + 1 - have > 16:
            raise ToolError("slot %s is far past %s's %d Session slots" % (slot, t.name, have))
        choices = list(t.available_input_routing_types)
        try:
            src = cs._track(k["source"])
            want = [r for r in choices if getattr(r, "attached_object", None) == src]
        except Exception:
            want = [r for r in choices if r.display_name == str(k["source"])]
        if len(want) != 1:
            raise ToolError("%s input %r: %d matches; choices %s" % (t.name, k["source"], len(want),
                                                                   [r.display_name for r in choices]))
        prep.append({"t": t, "slot": slot, "route": want[0], "channel": k.get("channel")})
    added = 0                                   # every check passed: now change the Set
    for p in prep:
        while p["slot"] >= len(list(p["t"].clip_slots)):
            cs._song.create_scene(-1)
            added += 1
        p["cslot"] = list(p["t"].clip_slots)[p["slot"]]
        if p["cslot"].has_clip:
            raise ToolError("slot %s of %s already holds a clip" % (p["slot"], p["t"].name))
    for p in prep:
        p["t"].input_routing_type = p["route"]
    rec = {"phase": "routing", "done": False, "error": None, "takes": [{"dst": cs._ref(p["t"])} for p in prep]}
    _RECA["multi"] = rec

    def tick():
        if _RECA.get("multi") is not rec or rec["done"]:
            return
        try:
            if rec["phase"] == "routing":
                for p, r in zip(prep, rec["takes"]):
                    t = p["t"]
                    if p["channel"] is not None:
                        chs = [c for c in t.available_input_routing_channels if c.display_name == p["channel"]]
                        if len(chs) != 1:
                            raise ToolError("%s channel %r not offered" % (t.name, p["channel"]))
                        t.input_routing_channel = chs[0]
                    t.current_monitoring_state = 2
                    t.arm = True
                    r.update(input=t.input_routing_type.display_name, channel=t.input_routing_channel.display_name,
                             slot=p["slot"])
                rec["phase"] = "launch"
            elif rec["phase"] == "launch":
                for p in prep:
                    p["cslot"].fire(record_length=length)
                rec["phase"] = "recording"
            elif rec["phase"] == "recording":
                for p, r in zip(prep, rec["takes"]):
                    c = p["cslot"].clip
                    if c is not None and c.is_recording:
                        r["started"] = True
                    if r.get("started") and not r.get("done") and c is not None and not c.is_recording:
                        p["t"].arm = False
                        fp = c.file_path or ""
                        r.update(done=True, clip_length=c.length, file=fp)
                        if "Temp Project" in fp or "/Live Recordings/" in fp:
                            r["warning"] = "recorded outside this Set's project: save the Set in a project folder"
                if all(r.get("done") for r in rec["takes"]):
                    rec.update(phase="done", done=True)
                    return
            cs.schedule_message(1, tick)
        except Exception as e:
            for p in prep:
                p["t"].arm = False
            rec.update(phase="done", done=True, error="%s: %s" % (type(e).__name__, e))

    cs.schedule_message(1, tick)
    return {"started": True, "takes": len(prep), "scenes_added": added, "bars": bars, "beats": length}


def cmd_record_tracks_audio_status(cs):
    rec = _RECA.get("multi")
    if rec is None:
        raise ToolError("no multi-track recording started")
    return dict(rec)


# ------------------------------------------------------------------------------------- MIDI notes: velocity and expression
# Live 11+ note API: Clip.get_all_notes_extended() returns MidiNote objects that carry a note_id;
# Clip.apply_note_modifications(notes) writes their changed attributes back, matched by id. These commands read notes
# and change their expression only: nothing is added, removed, moved or lengthened.
# Ranges: velocity 1-127, probability 0-1 (Live's Chance), velocity_deviation -127..127 (Live's Velocity Range: the
# random spread Live adds on each play), release_velocity 0-127.
_NOTE_RANGES = {"velocity": (1.0, 127.0), "probability": (0.0, 1.0), "velocity_deviation": (-127.0, 127.0),
                "release_velocity": (0.0, 127.0)}
_GRID_TOL = 0.02     # beats: how far from the grid a note may start and still count as on it (a 32nd is 0.125)
_EPS = 1e-6


def _note_dict(n):
    return {"id": int(n.note_id), "pitch": int(n.pitch), "start": float(n.start_time), "duration": float(n.duration),
            "velocity": float(n.velocity), "mute": bool(n.mute), "probability": float(n.probability),
            "velocity_deviation": float(n.velocity_deviation), "release_velocity": float(n.release_velocity)}


def _live_notes(c):
    if c.is_audio_clip:
        raise ToolError("%r is an audio clip: notes are on MIDI clips" % c.name)
    get_all = getattr(c, "get_all_notes_extended", None)
    if get_all is not None:
        return get_all()
    return c.get_notes_extended(0, 128, -16384.0, 1048576.0)


def _as_list(v):
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _select_notes(notes, ids=None, pitch=None, pitch_range=None, start=None, end=None, every=None, offset=0.0,
                  tolerance=_GRID_TOL):
    """Pure. The notes (dicts from _note_dict) that pass every filter given, in time order, then pitch. start, end,
    every and offset are beats already. A note is on the grid when its start is within `tolerance` of
    offset + k * every."""
    want = None if ids is None else set(int(i) for i in _as_list(ids))
    pitches = None if pitch is None else set(int(p) for p in _as_list(pitch))
    lo = hi = None
    if pitch_range is not None:
        if not (isinstance(pitch_range, (list, tuple)) and len(pitch_range) == 2):
            raise ToolError("pitch_range is [low, high], both inclusive")
        lo, hi = int(pitch_range[0]), int(pitch_range[1])
        if lo > hi:
            raise ToolError("pitch_range low %d is above high %d" % (lo, hi))
    if every is not None and not float(every) > 0:
        raise ToolError("every must be more than 0 beats, got %r" % every)
    if start is not None and end is not None and not start < end:
        raise ToolError("start %g must be before end %g" % (start, end))
    tol = float(tolerance)
    out = []
    for n in notes:
        if want is not None and n["id"] not in want:
            continue
        if pitches is not None and n["pitch"] not in pitches:
            continue
        if lo is not None and not lo <= n["pitch"] <= hi:
            continue
        if start is not None and n["start"] < start - _EPS:
            continue
        if end is not None and n["start"] >= end - _EPS:
            continue
        if every is not None:
            r = (n["start"] - float(offset)) % float(every)
            if min(r, float(every) - r) > tol + _EPS:
                continue
        out.append(n)
    out.sort(key=lambda n: (n["start"], n["pitch"]))
    return out


def _check_range(name, v, lo, hi):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ToolError("%s must be a number, got %r" % (name, v))
    if not lo <= x <= hi:
        raise ToolError("%s %r is outside %g..%g" % (name, v, lo, hi))
    return x


def _plan_expression(sel, velocity=None, velocity_pattern=None, velocity_ramp=None, velocity_scale=None,
                     velocity_add=None, humanize=None, seed=0, probability=None, velocity_deviation=None,
                     release_velocity=None, mute=None):
    """Pure. For each selected note: the attributes to write, before and after. Returns (plan, clamped).

    Velocity, in this order: one base (velocity; or velocity_pattern, cycled once per onset in time order, so the
    notes of a chord share a step; or velocity_ramp [from, to], linear from the first onset to the last), then
    velocity_scale, then velocity_add, then humanize (a seeded random +/- amount per note, so the same call gives
    the same result). The result is rounded and kept in 1-127; `clamped` counts the notes that had to be kept.
    probability, velocity_deviation, release_velocity and mute are set as given; a value out of range is an error."""
    bases = [k for k, v in (("velocity", velocity), ("velocity_pattern", velocity_pattern),
                            ("velocity_ramp", velocity_ramp)) if v is not None]
    if len(bases) > 1:
        raise ToolError("give one of velocity, velocity_pattern or velocity_ramp, not %s" % " and ".join(bases))
    if velocity is not None:
        velocity = _check_range("velocity", velocity, 1, 127)
    if velocity_pattern is not None:
        if not isinstance(velocity_pattern, (list, tuple)) or not velocity_pattern:
            raise ToolError("velocity_pattern is a list of velocities, e.g. [110, 70, 85]")
        velocity_pattern = [_check_range("velocity_pattern value", v, 1, 127) for v in velocity_pattern]
    if velocity_ramp is not None:
        if not (isinstance(velocity_ramp, (list, tuple)) and len(velocity_ramp) == 2):
            raise ToolError("velocity_ramp is [from, to], e.g. [60, 120]")
        velocity_ramp = [_check_range("velocity_ramp value", v, 1, 127) for v in velocity_ramp]
    if velocity_scale is not None:
        velocity_scale = _check_range("velocity_scale", velocity_scale, 0, 16)
    if velocity_add is not None:
        velocity_add = _check_range("velocity_add", velocity_add, -127, 127)
    if humanize is not None:
        humanize = _check_range("humanize", humanize, 0, 64)
    other = {}
    for k, v in (("probability", probability), ("velocity_deviation", velocity_deviation),
                 ("release_velocity", release_velocity)):
        if v is not None:
            other[k] = _check_range(k, v, *_NOTE_RANGES[k])
    has_vel = bool(bases) or any(v is not None for v in (velocity_scale, velocity_add, humanize))
    if not has_vel and not other and mute is None:
        raise ToolError("nothing to change: give a velocity change (velocity, velocity_pattern, velocity_ramp, "
                        "velocity_scale, velocity_add, humanize), probability, velocity_deviation, release_velocity "
                        "or mute")
    onsets = sorted(set(round(n["start"], 6) for n in sel))
    step = dict((t, i) for i, t in enumerate(onsets))
    t0, t1 = (onsets[0], onsets[-1]) if onsets else (0.0, 0.0)
    rng = random.Random(int(seed))
    plan, clamped = [], 0
    for n in sel:
        after = {}
        if has_vel:
            at = round(n["start"], 6)
            v = n["velocity"]
            if velocity is not None:
                v = velocity
            elif velocity_pattern is not None:
                v = velocity_pattern[step[at] % len(velocity_pattern)]
            elif velocity_ramp is not None:
                a, b = velocity_ramp
                v = a if t1 == t0 else a + (b - a) * (at - t0) / (t1 - t0)
            if velocity_scale is not None:
                v *= velocity_scale
            if velocity_add is not None:
                v += velocity_add
            if humanize:
                v += rng.uniform(-humanize, humanize)
            r = int(math.floor(v + 0.5))
            kept = min(127, max(1, r))
            if kept != r:
                clamped += 1
            after["velocity"] = float(kept)
        after.update(other)
        if mute is not None:
            after["mute"] = bool(mute)
        before = dict((k, n[k]) for k in after)
        changed = any((before[k] != after[k]) if k == "mute" else abs(before[k] - after[k]) > 1e-9 for k in after)
        plan.append({"id": n["id"], "pitch": n["pitch"], "start": n["start"], "before": before, "after": after,
                     "changed": changed})
    return plan, clamped


def _velocity_summary(sel, beats_per_bar, tolerance=_GRID_TOL):
    """Velocity range and mean, and the mean velocity at each 16th of the bar (notes within `tolerance` of a 16th)."""
    if not sel:
        return {"count": 0}
    vels = [n["velocity"] for n in sel]
    steps = {}
    for n in sel:
        pos = n["start"] % beats_per_bar
        k = int(math.floor(pos / 0.25 + 0.5))
        if abs(pos - k * 0.25) <= tolerance + _EPS:
            steps.setdefault(k % max(1, int(round(beats_per_bar / 0.25))), []).append(n["velocity"])
    return {"count": len(sel), "velocity_min": min(vels), "velocity_max": max(vels),
            "velocity_mean": round(sum(vels) / len(vels), 2), "distinct_velocities": len(set(vels)),
            "muted": sum(1 for n in sel if n["mute"]),
            "below_full_chance": sum(1 for n in sel if n["probability"] < 1.0 - 1e-9),
            "velocity_by_16th": [[k + 1, round(sum(v) / len(v), 2), len(v)] for k, v in sorted(steps.items())]}


def _note_filters(cs, start, end, every, offset):
    return (None if start is None else _beats(cs, start), None if end is None else _beats(cs, end),
            None if every is None else _beats(cs, every), _beats(cs, offset or 0))


def cmd_get_clip_notes(cs, track, slot=None, arrangement_index=None, pitch=None, pitch_range=None, start=None,
                       end=None, every=None, offset=0, tolerance=_GRID_TOL, limit=2000):
    """A MIDI clip's notes (Session slot or Arrangement index) with their ids and expression, in clip beats, and a
    velocity summary. Filters, all optional and combined: pitch (one or a list), pitch_range [low, high], start/end
    (clip positions, [start, end)), every/offset in beats (notes on a grid: every=0.5, offset=0.25 is the off-beat
    16ths)."""
    t, c = _any_clip(cs, track, slot, arrangement_index)
    s, e, ev, off = _note_filters(cs, start, end, every, offset)
    notes = [_note_dict(n) for n in _live_notes(c)]
    sel = _select_notes(notes, None, pitch, pitch_range, s, e, ev, off, tolerance)
    lim = max(0, int(limit))
    return {"track": cs._ref(t), "clip": c.name, "length": c.length, "total_notes": len(notes), "matched": len(sel),
            "truncated": len(sel) > lim, "summary": _velocity_summary(sel, _beats_per_bar(cs), float(tolerance)),
            "notes": sel[:lim]}


def cmd_set_note_expression(cs, track, slot=None, arrangement_index=None, ids=None, pitch=None, pitch_range=None,
                            start=None, end=None, every=None, offset=0, tolerance=_GRID_TOL, velocity=None,
                            velocity_pattern=None, velocity_ramp=None, velocity_scale=None, velocity_add=None,
                            humanize=None, seed=0, probability=None, velocity_deviation=None, release_velocity=None,
                            mute=None, dry_run=False, limit=500):
    """Change the velocity and expression of a MIDI clip's existing notes, chosen with the same filters as
    get_clip_notes plus ids. Nothing is added, removed or moved. Every changed note is read back; a note that reads
    back different is an error that names it. dry_run=True returns the plan and writes nothing. No match is an
    error, and nothing is written."""
    t, c = _any_clip(cs, track, slot, arrangement_index)
    s, e, ev, off = _note_filters(cs, start, end, every, offset)
    live = _live_notes(c)
    notes = [_note_dict(n) for n in live]
    sel = _select_notes(notes, ids, pitch, pitch_range, s, e, ev, off, tolerance)
    if not sel:
        raise ToolError("no notes matched in %r (%d notes in the clip); nothing written" % (c.name, len(notes)))
    plan, clamped = _plan_expression(sel, velocity, velocity_pattern, velocity_ramp, velocity_scale, velocity_add,
                                     humanize, seed, probability, velocity_deviation, release_velocity, mute)
    todo = [p for p in plan if p["changed"]]
    lim = max(0, int(limit))
    res = {"track": cs._ref(t), "clip": c.name, "matched": len(sel), "changed": len(todo),
           "unchanged": len(plan) - len(todo), "clamped": clamped, "dry_run": bool(dry_run)}
    if dry_run or not todo:
        res.update(written=False, notes=plan[:lim], truncated=len(plan) > lim)
        return res
    by_id = dict((int(n.note_id), n) for n in live)
    for p in todo:
        n = by_id[p["id"]]
        for k, v in p["after"].items():
            setattr(n, k, v)
    c.apply_note_modifications(live)
    back = dict((d["id"], d) for d in (_note_dict(n) for n in _live_notes(c)))
    bad = []
    for p in todo:
        d = back.get(p["id"])
        if d is None:
            bad.append({"id": p["id"], "problem": "the note is gone"})
            continue
        for k, v in p["after"].items():
            if (d[k] != v) if k == "mute" else abs(d[k] - v) > 1e-3:
                bad.append({"id": p["id"], "attribute": k, "wanted": v, "read_back": d[k]})
    if bad:
        raise ToolError("written, but %d values read back different: %s" % (len(bad), bad[:20]))
    res.update(written=True, read_back="every changed note matches",
               notes=[dict(p, after=dict((k, back[p["id"]][k]) for k in p["after"])) for p in todo[:lim]],
               truncated=len(todo) > lim)
    return res


# ------------------------------------------------------------------------------------- quantize
# Quantize moves notes toward a grid through the same note API as set_note_expression (apply_note_modifications,
# matched by note_id), so it takes the same note selection, any grid, a strength and MPC-style swing, and every
# moved note is read back. Live's own Clip.quantize has fixed grids and no selection.
_NOTE_VALUES = {"1/1": 4.0, "1/2": 2.0, "1/4": 1.0, "1/8": 0.5, "1/16": 0.25, "1/32": 0.125, "1/2t": 4.0 / 3,
                "1/4t": 2.0 / 3, "1/8t": 1.0 / 3, "1/16t": 1.0 / 6, "1/32t": 1.0 / 12}


def _grid_beats(cs, grid):
    """A grid as a note value ("1/16", "1/8T") or in beats (0.25, "0.25b")."""
    if isinstance(grid, str) and grid.strip().lower() in _NOTE_VALUES:
        return _NOTE_VALUES[grid.strip().lower()]
    if isinstance(grid, str) and "/" in grid:
        raise ToolError("grid %r: use a note value (%s) or beats (0.25)" % (grid, ", ".join(sorted(_NOTE_VALUES))))
    return _beats(cs, grid)


def _swung(k, grid, swing):
    """Where grid step k lands with swing (percent; 50 = straight, about 66 = triplet feel): every second step moves
    later, to `swing` percent of its pair of steps."""
    pair = k // 2
    if k % 2 == 0:
        return pair * 2.0 * grid
    return pair * 2.0 * grid + 2.0 * grid * swing / 100.0


def _nearest_step(t, grid, swing):
    k0 = int(math.floor(t / grid))
    best = None
    for k in range(k0 - 1, k0 + 3):
        p = _swung(k, grid, swing)
        if best is None or abs(p - t) < abs(best - t) - 1e-12:
            best = p
    return best


_SAME_SPOT = 1e-4     # beats: Live stores note times in single precision, so "the same start" needs a tolerance


def _collisions(rows):
    """Pure. rows (id, pitch, start): the pairs of one pitch that start at the same spot."""
    out = []
    srt = sorted(rows, key=lambda r: (r[1], r[2]))
    for a, b in zip(srt, srt[1:]):
        if a[1] == b[1] and abs(a[2] - b[2]) < _SAME_SPOT:
            out.append({"pitch": a[1], "start": a[2], "ids": [a[0], b[0]]})
    return out


def _settle(plan, notes):
    """Pure. Live keeps notes of one pitch from overlapping: a note that would run past the start of the next note of
    its pitch is shortened to end there (measured 2026-11-27: a swung 0.2-beat hat became 0.17). Returns the plan
    with those trims predicted, including notes outside the selection that a moved note now cuts short."""
    planned = dict((p["id"], p) for p in plan)
    final = []
    for n in notes:
        p = planned.get(n["id"])
        st, du = (p["after"]["start"], p["after"]["duration"]) if p else (n["start"], n["duration"])
        final.append((n["pitch"], st, du, n))
    final.sort(key=lambda r: (r[0], r[1]))
    extra = []
    for a, b in zip(final, final[1:]):
        if a[0] != b[0] or a[1] + a[2] <= b[1] + 1e-6:
            continue
        d = round(b[1] - a[1], 9)
        n = a[3]
        p = planned.get(n["id"])
        if p is not None:
            p["after"]["duration"] = d
            p["trimmed"] = True
            p["changed"] = True
        else:
            extra.append({"id": n["id"], "pitch": n["pitch"], "before": {"start": n["start"], "duration": n["duration"]},
                          "after": {"start": n["start"], "duration": d}, "moved": 0.0, "changed": True,
                          "trimmed": True, "selected": False})
    return plan + extra


def _plan_quantize(sel, grid, strength=100, swing=50, ends=False):
    """Pure. For each selected note: its start (and with ends=True its end) moved toward the nearest grid step by
    `strength` percent. Without ends the length is kept. Returns (plan, report); report["collisions"] lists pairs of
    one pitch that would land on the same start, which Live would merge (the command then writes nothing)."""
    grid = _check_range("grid", grid, 1.0 / 64, 16)
    strength = _check_range("strength", strength, 0, 100)
    swing = _check_range("swing", swing, 50, 75)
    plan, err_before, err_after = [], [], []
    for n in sel:
        s0, d0 = n["start"], n["duration"]
        t0 = _nearest_step(s0, grid, swing)
        s1 = round(s0 + (t0 - s0) * strength / 100.0, 9)
        if ends:
            e0 = s0 + d0
            e1 = round(e0 + (_nearest_step(e0, grid, swing) - e0) * strength / 100.0, 9)
            d1 = round(e1 - s1, 9) if e1 > s1 + 1e-6 else d0     # an end can't reach its start: keep the length
        else:
            d1 = d0
        err_before.append(abs(s0 - t0))
        err_after.append(abs(s1 - _nearest_step(s1, grid, swing)))
        after = {"start": s1, "duration": d1}
        changed = abs(s1 - s0) > 1e-9 or abs(d1 - d0) > 1e-9
        plan.append({"id": n["id"], "pitch": n["pitch"], "before": {"start": s0, "duration": d0}, "after": after,
                     "moved": round(s1 - s0, 6), "changed": changed})
    report = {"collisions": _collisions([(p["id"], p["pitch"], p["after"]["start"]) for p in plan]),"grid": grid, "strength": strength, "swing": swing, "ends": bool(ends),
              "mean_off_grid_before": round(sum(err_before) / len(err_before), 6) if plan else 0.0,
              "mean_off_grid_after": round(sum(err_after) / len(err_after), 6) if plan else 0.0,
              "largest_move": round(max([abs(p["moved"]) for p in plan] or [0.0]), 6)}
    return plan, report


def cmd_quantize_notes(cs, track, slot=None, arrangement_index=None, grid=0.25, strength=100, swing=50, ends=False,
                       ids=None, pitch=None, pitch_range=None, start=None, end=None, every=None, offset=0,
                       tolerance=_GRID_TOL, dry_run=False, limit=500):
    """Move a MIDI clip's notes toward a grid (beats: 0.25 = 16ths, 1/3 = 8th-note triplets) by `strength` percent,
    with optional swing (50 = straight, about 66 = triplet feel) and note ends. Notes are chosen with the
    get_clip_notes filters or ids. Pitch, velocity and the other notes don't change. Every moved note is read
    back; dry_run=True returns the plan and writes nothing."""
    t, c = _any_clip(cs, track, slot, arrangement_index)
    s, e, ev, off = _note_filters(cs, start, end, every, offset)
    live = _live_notes(c)
    notes = [_note_dict(n) for n in live]
    sel = _select_notes(notes, ids, pitch, pitch_range, s, e, ev, off, tolerance)
    if not sel:
        raise ToolError("no notes matched in %r (%d notes in the clip); nothing written" % (c.name, len(notes)))
    plan, report = _plan_quantize(sel, _grid_beats(cs, grid), strength, swing, ends)
    picked = set(p["id"] for p in plan)
    rows = [(p["id"], p["pitch"], p["after"]["start"]) for p in plan]
    rows += [(n["id"], n["pitch"], n["start"]) for n in notes if n["id"] not in picked]
    hit = [c for c in _collisions(rows) if not set(c["ids"]) <= picked]   # landing on a note that isn't selected
    clashes = report["collisions"] + hit
    report["collisions"] = clashes
    if clashes and not dry_run:
        raise ToolError("%d pairs of notes would land on the same spot (same pitch, same start)%s and Live would "
                        "merge them; nothing written. Use a finer grid, a lower strength or a narrower selection "
                        "(dry_run=True shows the plan): %s" % (len(clashes), ", some outside the selection" if hit
                                                               else "", clashes[:10]))
    if not clashes:
        plan = _settle(plan, notes)
    todo = [p for p in plan if p["changed"]]
    lim = max(0, int(limit))
    res = dict(report, track=cs._ref(t), clip=c.name, matched=len(sel), changed=len(todo),
               unchanged=len(plan) - len(todo), dry_run=bool(dry_run),
               shortened=[p["id"] for p in plan if p.get("trimmed")],
               shortened_outside_selection=[p["id"] for p in plan if p.get("selected") is False])
    if dry_run or not todo:
        res.update(written=False, notes=plan[:lim], truncated=len(plan) > lim)
        return res
    by_id = dict((int(n.note_id), n) for n in live)
    for p in todo:
        n = by_id[p["id"]]
        n.start_time = p["after"]["start"]
        n.duration = p["after"]["duration"]
    c.apply_note_modifications(live)
    back = dict((d["id"], d) for d in (_note_dict(n) for n in _live_notes(c)))
    bad = []
    for p in todo:
        d = back.get(p["id"])
        if d is None:
            bad.append({"id": p["id"], "problem": "the note is gone"})
        elif abs(d["start"] - p["after"]["start"]) > 1e-4 or abs(d["duration"] - p["after"]["duration"]) > 1e-4 \
                or d["pitch"] != p["pitch"]:
            bad.append({"id": p["id"], "wanted": p["after"], "read_back": {"start": d["start"],
                                                                         "duration": d["duration"], "pitch": d["pitch"]}})
    if len(back) != len(notes):
        bad.append({"problem": "the clip had %d notes and now has %d" % (len(notes), len(back))})
    if bad:
        raise ToolError("written, but %d notes read back different: %s" % (len(bad), bad[:20]))
    res.update(written=True, read_back="every moved note matches",
               notes=[dict(p, after={"start": back[p["id"]]["start"], "duration": back[p["id"]]["duration"]})
                      for p in todo[:lim]], truncated=len(todo) > lim)
    return res


# ------------------------------------------------------------------------------------- groove pool
# Song.groove_pool.grooves (Live 11+): each Groove has name, base, and timing / random / velocity / quantize amounts
# in percent (measured 2026-11-27, Live 12.4.16). A groove gets into the pool by loading its .agr file from the
# browser (it lands in the pool; no clip changes); Clip.groove assigns one to a clip; Song.groove_amount is the
# pool's Global Amount.
_GROOVE_BASES = ("1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32")    # Groove.base index; measured: 1 = 8ths, 3 = 16ths
_GROOVE_RANGES = {"timing": (0.0, 100.0), "random": (0.0, 100.0), "velocity": (-100.0, 100.0),
                  "quantize": (0.0, 100.0)}
_GROOVE_ATTRS = {"timing": "timing_amount", "random": "random_amount", "velocity": "velocity_amount",
                 "quantize": "quantization_amount"}
_GROOVE_ROOTS = (("Core Library", ("packs", "Core Library", "Grooves")), ("User Library", ("user_library", "Grooves")))


def _pool(cs):
    return list(cs._song.groove_pool.grooves)


def _groove_out(i, g):
    b = int(g.base)
    out = {"index": i, "name": g.name, "base": _GROOVE_BASES[b] if 0 <= b < len(_GROOVE_BASES) else b}
    for k, a in _GROOVE_ATTRS.items():
        out[k] = float(getattr(g, a))
    return out


def _groove_index(pool, g):
    for i, x in enumerate(pool):
        if x == g:
            return i
    return None


def _groove(cs, ref):
    pool = _pool(cs)
    if not pool:
        raise ToolError("the groove pool is empty: load a groove first (list_grooves, load_groove)")
    if isinstance(ref, bool):
        raise ToolError("groove is an index or a name")
    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        i = int(ref)
        if not 0 <= i < len(pool):
            raise ToolError("groove %d out of range: the pool has %d" % (i, len(pool)))
        return i, pool[i]
    key = str(ref).strip().lower()
    hits = [(i, g) for i, g in enumerate(pool) if g.name.lower() == key]
    if len(hits) != 1:
        raise ToolError("%d grooves called %r in the pool; use its index: %s"
                        % (len(hits), ref, [_groove_out(i, g) for i, g in enumerate(pool)]))
    return hits[0]


def cmd_get_groove_pool(cs, clips=False):
    """The groove pool: every groove's index, name, base and amounts (percent), and the Global Amount. clips=True
    also lists every clip that has a groove assigned (Session and Arrangement)."""
    pool = _pool(cs)
    out = {"global_amount": float(cs._song.groove_amount), "count": len(pool),
           "grooves": [_groove_out(i, g) for i, g in enumerate(pool)]}
    if clips:
        uses = []
        for t in cs._song.tracks:
            spots = [({"slot": s}, sl.clip) for s, sl in enumerate(t.clip_slots) if sl.clip is not None]
            spots += [({"arrangement_index": i}, c) for i, c in enumerate(t.arrangement_clips)]
            for where, c in spots:
                g = getattr(c, "groove", None)
                if g is not None:
                    uses.append(dict(where, track=cs._ref(t), clip=c.name, groove=_groove_index(pool, g),
                                     groove_name=g.name))
        out["clips"] = uses
    return out


def cmd_set_groove(cs, groove, timing=None, random=None, velocity=None, quantize=None, base=None):
    """Change one pool groove (by index or name): timing, random, quantize 0-100 and velocity -100..100 (percent),
    base one of 1/4, 1/8, 1/8T, 1/16, 1/16T, 1/32. Every clip using the groove follows. Reads it back."""
    i, g = _groove(cs, groove)
    before = _groove_out(i, g)
    want = {}
    for k, v in (("timing", timing), ("random", random), ("velocity", velocity), ("quantize", quantize)):
        if v is not None:
            want[k] = _check_range(k, v, *_GROOVE_RANGES[k])
    b = None
    if base is not None:
        if str(base) not in _GROOVE_BASES:
            raise ToolError("base is one of %s, not %r" % (list(_GROOVE_BASES), base))
        b = _GROOVE_BASES.index(str(base))
    if not want and b is None:
        raise ToolError("nothing to change: give timing, random, velocity, quantize or base")
    for k, v in want.items():
        setattr(g, _GROOVE_ATTRS[k], v)
    if b is not None:
        g.base = b
    after = _groove_out(i, g)
    bad = [k for k, v in want.items() if abs(after[k] - v) > 1e-3] + (["base"] if b is not None and after["base"] != base else [])
    if bad:
        raise ToolError("written, but %s read back different: %s" % (bad, after))
    return {"before": before, "after": after}


def cmd_set_groove_amount(cs, amount):
    """The groove pool's Global Amount, in percent (0-131, as Live's dial). 0 turns every groove off."""
    a = _check_range("amount", amount, 0, 131.25)
    before = float(cs._song.groove_amount)
    cs._song.groove_amount = a / 100.0
    got = float(cs._song.groove_amount)
    if abs(got - a / 100.0) > 1e-4:
        raise ToolError("written, but the Global Amount reads back %g, not %g" % (got * 100.0, a))
    return {"before": round(before * 100.0, 3), "after": round(got * 100.0, 3)}


def cmd_set_clip_groove(cs, track, groove, slot=None, arrangement_index=None):
    """Assign a pool groove (index or name) to a clip. Reads it back. Live's API can't remove a clip's groove (the
    setter refuses None and there is no deleter, measured on 12.4.16): to switch a groove's effect off, set its
    amounts to 0 with set_groove, or turn the Global Amount down with set_groove_amount."""
    t, c = _any_clip(cs, track, slot, arrangement_index)
    pool = _pool(cs)
    old = getattr(c, "groove", None)
    before = None if old is None else {"index": _groove_index(pool, old), "name": old.name}
    i, g = _groove(cs, groove)
    c.groove = g
    now = getattr(c, "groove", None)
    if now is None or now != g:
        raise ToolError("written, but the clip's groove reads back %r" % (None if now is None else now.name))
    return {"track": cs._ref(t), "clip": c.name, "before": before, "after": {"index": i, "name": g.name}}


def _groove_items(cs):
    """Every loadable groove file in the browser's Core Library and User Library Grooves folders."""
    b = cs.application().browser
    out = []
    for source, path in _GROOVE_ROOTS:
        node = getattr(b, path[0], None)
        for name in path[1:]:
            node = None if node is None else next((c for c in node.children if c.name == name), None)
        if node is None:
            continue
        stack = [(node, ())]
        while stack:
            item, folder = stack.pop()
            for ch in item.children:
                if ch.is_loadable and ch.name.lower().endswith(".agr"):
                    out.append((source, "/".join(folder), ch))
                elif ch.is_folder and len(folder) < 4:
                    stack.append((ch, folder + (ch.name,)))
    return out


def cmd_list_grooves(cs, search=None, limit=300):
    """Groove files you can load: Live's Core Library grooves and your User Library's. search matches the name or
    folder; every word must appear, in any order (e.g. "mpc 16", "swing 8ths", "style funk"). Each has a
    name and folder for load_groove."""
    words = [] if search is None else str(search).lower().split()
    rows = []
    for source, folder, item in _groove_items(cs):
        name = item.name[:-4]
        hay = ("%s %s %s" % (source, folder.replace("/", " "), name)).lower()
        if any(w not in hay for w in words):
            continue
        rows.append({"name": name, "folder": folder, "source": source})
    rows.sort(key=lambda r: (r["source"], r["folder"], r["name"]))
    lim = max(0, int(limit))
    return {"count": len(rows), "truncated": len(rows) > lim, "grooves": rows[:lim]}


def cmd_load_groove(cs, name, folder=None):
    """Start loading a groove file into the pool by name (as list_grooves gives it; folder narrows a name found in
    several places). Asynchronous: the pool grows on Live's next tick (the MCP tool waits for it). No clip
    changes."""
    key = str(name).strip().lower()
    if key.endswith(".agr"):
        key = key[:-4]
    hits = [(s, f, it) for s, f, it in _groove_items(cs) if it.name[:-4].lower() == key
            and (folder is None or f.lower() == str(folder).strip().lower())]
    if not hits:
        raise ToolError("no groove called %r%s: see list_grooves" % (name, "" if folder is None else " in %s" % folder))
    if len(hits) > 1:
        raise ToolError("%d grooves called %r: give folder, one of %s" % (len(hits), name, [f for _, f, _ in hits]))
    source, f, item = hits[0]
    before = len(_pool(cs))
    cs.application().browser.load_item(item)
    return {"loading": item.name[:-4], "folder": f, "source": source, "pool_before": before}


# ------------------------------------------------------------------------------------- note-follow automation
def _note_number(v):
    """A note as a MIDI number, or a name in Live's naming (C3 = 60): "E1" = 40, "F#2" = 54, "Bb0" = 34."""
    import re
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return int(round(v))
    m = re.match(r"^([A-Ga-g])([#b]?)(-?\d+)$", str(v).strip())
    if not m:
        raise ToolError("note %r: use a MIDI number or a name like E1, F#2, Bb0 (Live's naming, C3 = 60)" % (v,))
    base = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}[m.group(1).lower()]
    return base + {"#": 1, "b": -1, "": 0}[m.group(2)] + (int(m.group(3)) + 2) * 12


def _follow_points(notes, transpose=0, lo=0.0, hi=127.0, chord="lowest", end=None):
    """Pure. One step per onset: the onset's lowest (or highest) unmuted note plus `transpose`, kept in lo..hi. The
    first value also covers the clip's start. Returns (points [(beat, value)], clamped)."""
    if chord not in ("lowest", "highest"):
        raise ToolError("chord is lowest or highest, not %r" % (chord,))
    by = {}
    for n in notes:
        if n.get("mute") or (end is not None and n["start"] >= end - 1e-9):
            continue
        at = round(n["start"], 6)
        by.setdefault(at, []).append(n["pitch"])
    if not by:
        raise ToolError("the clip has no notes to follow")
    pts, clamped = [], 0
    for at in sorted(by):
        v = (min if chord == "lowest" else max)(by[at]) + int(transpose)
        kept = min(hi, max(lo, v))
        clamped += kept != v
        if not pts or pts[-1][1] != float(kept):
            pts.append((at, float(kept)))
    if pts[0][0] > 0:
        pts.insert(0, (0.0, pts[0][1]))
    return pts, clamped


def _param_kind(p):
    """'hz' for a frequency parameter (its display ends in Hz), else 'note' (its raw value is a MIDI note)."""
    d = p.str_for_value(p.value).strip().lower()
    return "hz" if d.endswith("hz") else "note"


def cmd_follow_notes(cs, track, slot, target, transpose=0, chord="lowest"):
    """Make a pitch parameter follow a Session clip's notes: a step in the clip's envelope at every onset, set to the
    onset's lowest note plus `transpose` semitones (chord="highest" for the top note). A note parameter (raw value
    a MIDI note: Roar FB Note, Resonators I Note) gets the note; a frequency parameter (display in Hz: Spectral
    Resonator Freq. Hz, a filter's Frequency) gets the note's frequency (A4 = 440 Hz, MIDI 69). Replaces the
    parameter's envelope in that clip. Arrangement clips have no clip envelopes in Live's API."""
    t, clip, p, env = _envelope(cs, track, slot, target, create=True)
    if env is None:
        raise ToolError("Live gave no envelope for %s in that clip" % p.name)
    end = clip.loop_end if clip.looping else clip.end_marker
    notes = [_note_dict(n) for n in _live_notes(clip)]
    kind = _param_kind(p)
    if kind == "hz":
        pts, clamped = _follow_points(notes, transpose, 0, 127, chord, end)
        pts = [(b, float(_to_raw(cs, p, "%.3f Hz" % (440.0 * 2 ** ((v - 69) / 12.0)), "display"))) for b, v in pts]
    else:
        pts, clamped = _follow_points(notes, transpose, p.min, p.max, chord, end)
    import Live
    env.delete_events_in_range(0.0, end + 1e-6)
    for i, (b, v) in enumerate(pts):
        env.create_event(Live.Envelope.EnvelopeEvent(b, v))
        if i + 1 < len(pts):
            env.create_event(Live.Envelope.EnvelopeEvent(pts[i + 1][0], v))
    back = [_read(p, env, b) for b, _ in pts]
    bad = [dict(r, wanted=v) for r, (b, v) in zip(back, pts) if abs(r["raw"] - v) > 1e-3]
    if bad:
        raise ToolError("written, but %d steps read back different: %s" % (len(bad), bad[:10]))
    return {"track": cs._ref(t), "parameter": p.name, "kind": kind, "steps": len(pts), "transpose": int(transpose),
            "chord": chord, "clamped": clamped, "steps_read_back": [{"beat": r["beat"], "value": r["display"]}
                                                                  for r in back[:64]]}


# ------------------------------------------------------------------------------------- amp-feedback bass
# A tuned resonance fed back through distortion: the whine of an amp feeding back, tracking the bass. Stock devices,
# in one Audio Effect Rack after the instrument: Auto Filter (Vowel) -> Saturator (Waveshaper, DC filter) -> Spectral
# Resonator (the tuned whine) -> Roar (feedback tuned to the same note, through a shaper) -> EQ Eight (tilt) ->
# Limiter (-1 dB ceiling). Live's API can't route Spectral Resonator's or Roar's MIDI sidechain, so the resonance
# follows the notes through follow_notes: clip envelope steps on Spectral Resonator's Freq. Hz (its pitch control in
# this mode; its Note parameter didn't move the sound, measured) and on Roar's FB Note.
# Stability (measured 2026-11-27, Live 12.4.16, a saw bass peaking about -5 dBFS, and 6 dB hotter): Roar's loop
# self-oscillates once Feedback x Shaper 1 Amt is too high, and then keeps ringing after the notes stop, whatever
# Fb Gate says (growl at 55 % feedback rang at -15.8 dBFS in the rest bar; screaming at 80 % / 65 % at -4.5). The
# presets sit below that edge with margin: every rest bar decays below -90 dBFS. Raising Feedback or Shaper 1 Amt
# past a preset can make the chain ring; the Limiter then holds it at -1 dBFS but doesn't stop it.
_FB_CHAIN = ("Auto Filter", "Saturator", "Spectral Resonator", "Roar", "EQ Eight", "Limiter")
_FB_COMMON = {
    "Auto Filter": {"Filter Type": "Vowel"},
    "Saturator": {"Type": "Waveshaper", "Pre Dc Filter": "On"},
    "Roar": {"FB Time Mode": "Note", "Fb Gate On": "On"},
    "EQ Eight": {"8 Filter On A": "On", "8 Filter Type A": "High Shelf", "8 Frequency A": "3000 Hz"},
    "Limiter": {"Ceiling": "-1.0 dB"},
}
_FB_PRESETS = {
    "subtle": {
        "Auto Filter": {"Formant": "30 %", "Resonance": "25 %", "Drive": "0 %"},
        "Saturator": {"Drive": "3 dB", "WS Drive": "35 %", "WS Curve": "20 %", "WS Depth": "0 %", "Dry/Wet": "60 %"},
        "Spectral Resonator": {"Decay": "300 ms", "Dry Wet": "20 %"},
        "Roar": {"Shaper 1 Type": "Soft Sine", "Shaper 1 Amt": "20 %", "Feedback": "30 %", "Dry/Wet": "45 %"},
        "EQ Eight": {"8 Gain A": "-2 dB"},
    },
    "growl": {
        "Auto Filter": {"Formant": "55 %", "Resonance": "45 %", "Drive": "20 %"},
        "Saturator": {"Drive": "8 dB", "WS Drive": "60 %", "WS Curve": "45 %", "WS Depth": "20 %", "Dry/Wet": "85 %"},
        "Spectral Resonator": {"Decay": "600 ms", "Dry Wet": "35 %"},
        "Roar": {"Shaper 1 Type": "Tube Preamp", "Shaper 1 Amt": "45 %", "Drive": "6 dB", "Feedback": "40 %",
                 "Dry/Wet": "70 %"},
        "EQ Eight": {"8 Gain A": "-4 dB"},
    },
    "screaming": {
        "Auto Filter": {"Formant": "75 %", "Resonance": "65 %", "Drive": "40 %"},
        "Saturator": {"Drive": "14 dB", "WS Drive": "85 %", "WS Curve": "70 %", "WS Depth": "45 %",
                      "WS Period": "20 %", "Dry/Wet": "100 %"},
        "Spectral Resonator": {"Decay": "1200 ms", "Dry Wet": "50 %"},
        "Roar": {"Shaper 1 Type": "Diode Clipper", "Shaper 1 Amt": "40 %", "Drive": "12 dB", "Feedback": "45 %",
                 "Dry/Wet": "90 %"},
        "EQ Eight": {"8 Frequency A": "2500 Hz", "8 Gain A": "-6 dB"},
    },
}


def _fb_settings(preset, fb_note, overrides=None):
    """Pure. Every parameter the chain sets, per device: the common settings, the preset's, Roar's FB Note, then
    overrides ({device: {parameter: value}}) on top."""
    if preset not in _FB_PRESETS:
        raise ToolError("preset is one of %s, not %r" % (sorted(_FB_PRESETS), preset))
    out = {}
    for name in _FB_CHAIN:
        out[name] = dict(_FB_COMMON.get(name, {}))
        out[name].update(_FB_PRESETS[preset].get(name, {}))
    out["Roar"]["FB Note"] = float(fb_note)
    out["Spectral Resonator"]["Freq. Hz"] = "%.2f Hz" % (440.0 * 2 ** ((fb_note - 69) / 12.0))
    for dev, vals in (overrides or {}).items():
        if dev not in out:
            raise ToolError("overrides: no device %r in the chain %s" % (dev, list(_FB_CHAIN)))
        out[dev].update(vals)
    return out


def cmd_build_feedback_bass(cs, track, preset="growl", key_note="E1", transpose=24, follow_slot=None,
                            overrides=None):
    """Put the amp-feedback bass chain after a track's bass, in one Audio Effect Rack named "Feedback Bass
    (preset)": Auto Filter (Vowel) -> Saturator (Waveshaper) -> Spectral Resonator (the tuned whine) -> Roar (tuned
    feedback) -> EQ Eight (tilt) -> Limiter (-1 dB). preset: subtle, growl or screaming. The resonance is tuned to
    key_note + transpose semitones (Live's naming, C3 = 60; Roar's range C-1..C5). follow_slot: a Session clip on
    this track whose notes the resonance then follows (follow_notes on Spectral Resonator's Freq. Hz and Roar's FB
    Note). overrides: {device: {parameter: value}} on top of the preset. Every setting is read back."""
    t = cs._track(track)
    devs = list(t.devices)
    if any(d.name.startswith("Feedback Bass") for d in devs):
        raise ToolError("%s already has a Feedback Bass rack: use another track or remove it first" % t.name)
    if t.has_midi_input and not any(int(getattr(d, "type", 0) or 0) == 1 for d in devs):
        raise ToolError("%s is a MIDI track with no instrument: load the bass first (the chain goes after it)" % t.name)
    fb = _note_number(key_note) + int(transpose)
    if not 12 <= fb <= 84:
        raise ToolError("key_note + transpose is MIDI note %d, outside Roar's FB Note range 12..84 (C-1..C5)" % fb)
    settings = _fb_settings(preset, fb, overrides)
    rack = t.insert_device("Audio Effect Rack")
    rack.name = "Feedback Bass (%s)" % preset
    ch = rack.insert_chain()
    if ch is None:
        ch = list(rack.chains)[-1]
    ch.name = "Feedback"
    for name in _FB_CHAIN:
        ch.insert_device(name)
    chain_devs = list(ch.devices)
    if [d.name for d in chain_devs] != list(_FB_CHAIN):
        raise ToolError("the chain came out as %s (rack %r left on %s)" % ([d.name for d in chain_devs], rack.name,
                                                                           t.name))
    report = []
    for d in chain_devs:
        for pname, val in settings[d.name].items():
            r = cs._set_param(cs._param(d, pname), val, "auto")
            report.append({"device": d.name, "parameter": pname, "set": val, "reads": r["after"]["display"]})
    ri = list(t.devices).index(rack)
    targets = [{"device": ri, "chain": "0", "chain_device": _FB_CHAIN.index(d), "parameter": p}
               for d, p in (("Spectral Resonator", "Freq. Hz"), ("Roar", "FB Note"))]
    roar = chain_devs[_FB_CHAIN.index("Roar")]
    out = {"track": cs._ref(t), "rack": rack.name, "rack_index": ri, "chain": [d.name for d in chain_devs],
           "preset": preset, "tuned_to": {"midi": fb, "name": cs._param(roar, "FB Note").str_for_value(fb)},
           "settings": report, "follow_targets": targets}
    if follow_slot is not None:
        out["follow"] = [cmd_follow_notes(cs, track, follow_slot, x, transpose=transpose) for x in targets]
    return out
