#!/usr/bin/env python3
"""Export audio from Live through its own Export Audio/Video window, driven by macOS Accessibility in the background
(Live is not brought to the front and the screen isn't taken over). Live's API has no render call; this is the
offline (faster than real time) render.

run: uv run -q --with pyobjc-framework-ApplicationServices --with pyobjc-framework-Cocoa python tools/live_export.py \
       --start 9.1.1 --length 8.0.0 --out "/abs/folder/Name.wav" [--option "Normalize=off" ...]

Steps: File > Export Audio/Video (menu, by Accessibility) -> each range field stepped with its own increment and
decrement actions until it reads the target (read back, so a wrong value can't slip through) -> optional on/off
switches set and read back -> Export -> in the save panel: Go to Folder (cmd+shift+G) for the folder, the file name,
Save -> wait for the file to appear and stop growing. Refuses a path that already exists (no "Replace?" sheet).
Prints one JSON object. Needs Accessibility permission for the process that runs it (the Claude app has it).
Measured 2026-11-12 on Live 12.4.16: 8 bars at 140 BPM exported in seconds, 13.7143 s, 48 kHz 24-bit.
"""
import argparse, json, os, sys, time

from AppKit import NSRunningApplication
from ApplicationServices import (AXUIElementCopyAttributeValue, AXUIElementCreateApplication,
                                 AXUIElementPerformAction, AXUIElementSetAttributeValue,
                                 AXUIElementSetMessagingTimeout)
from Quartz import (CGEventCreateKeyboardEvent, CGEventPostToPid, CGEventSetFlags, kCGEventFlagMaskCommand,
                    kCGEventFlagMaskShift)

BUNDLE = "com.ableton.live"
FIELDS = ("Bar", "Beat", "Sixteenths")


class ExportError(Exception):
    pass


def attr(e, a):
    err, v = AXUIElementCopyAttributeValue(e, a, None)
    return v if err == 0 else None


def kids(e):
    return list(attr(e, "AXChildren") or [])


def wait_for(fn, timeout, what):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = fn()
        if v:
            return v
        time.sleep(0.1)
    raise ExportError("timed out after %gs waiting for %s" % (timeout, what))


def live_app():
    apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(BUNDLE)
    if not apps:
        raise ExportError("Live isn't running")
    pid = apps[0].processIdentifier()
    app = AXUIElementCreateApplication(pid)
    AXUIElementSetMessagingTimeout(app, 3.0)
    return pid, app


def window(app, title):
    for w in attr(app, "AXWindows") or []:
        if (attr(w, "AXTitle") or "") == title:
            return w
    return None


def press_menu(app, path):
    cur = attr(app, "AXMenuBar")
    for name in path:
        hit = None
        for k in kids(cur):
            if attr(k, "AXRole") == "AXMenu":
                hit = next((m for m in kids(k) if (attr(m, "AXTitle") or "") == name), None)
            elif (attr(k, "AXTitle") or "") == name:
                hit = k
            if hit is not None:
                break
        if hit is None:
            raise ExportError("no menu item %r" % name)
        cur = hit
    if not attr(cur, "AXEnabled"):
        raise ExportError("menu item %s is disabled (is a dialog already open in Live?)" % " > ".join(path))
    AXUIElementPerformAction(cur, "AXPress")


def controls(win):
    g = kids(win)[0]
    return {attr(k, "AXDescription"): k for k in kids(g) if attr(k, "AXDescription")}


def step_to(el, target, name):
    """Step a Live number field to `target` with AXIncrement/AXDecrement, reading it back after each step."""
    for _ in range(4000):
        v = attr(el, "AXValue")
        if v is None:
            raise ExportError("can't read %s" % name)
        v = int(round(float(v)))
        if v == target:
            return v
        AXUIElementPerformAction(el, "AXIncrement" if v < target else "AXDecrement")
    raise ExportError("%s didn't reach %s" % (name, target))


def parse_pos(s, length=False):
    parts = [int(p) for p in str(s).strip().split(".")]
    while len(parts) < 3:
        parts.append(0 if length else 1)
    if length and parts == [0, 0, 0]:
        raise ExportError("length is zero")
    return parts[:3]


def key(pid, code, flags=0):
    for down in (True, False):
        e = CGEventCreateKeyboardEvent(None, code, down)
        if flags:
            CGEventSetFlags(e, flags)
        CGEventPostToPid(pid, e)
        time.sleep(0.03)


def export(start, length, out, options=None, timeout=1800):
    out = os.path.abspath(os.path.expanduser(out))
    folder, name = os.path.split(out)
    if not os.path.isdir(folder):
        raise ExportError("folder doesn't exist: %s" % folder)
    if os.path.exists(out):
        raise ExportError("%s already exists: pick another name (nothing exported)" % out)
    if not name.lower().endswith((".wav", ".aif", ".aiff", ".flac")):
        raise ExportError("name must end in .wav, .aif, .aiff or .flac (it should match the File Type setting)")
    pid, app = live_app()
    if window(app, "Export Audio/Video") is None:
        press_menu(app, ["File", "Export Audio/Video..."])
    win = wait_for(lambda: window(app, "Export Audio/Video"), 10, "the Export Audio/Video window")
    c = wait_for(lambda: controls(win) or None, 5, "the export controls")
    report = {"range": {}, "options": {}}
    try:
        for label, vals in (("Start", parse_pos(start)), ("Length", parse_pos(length, True))):
            got = []
            for unit, v in zip(FIELDS, vals):
                n = "%s of Rendered Audio File (%s)" % (label, unit)
                if n not in c:
                    raise ExportError("no field %r in the export window" % n)
                got.append(step_to(c[n], v, n))
            report["range"][label.lower()] = ".".join(str(x) for x in got)
        for opt, want in (options or {}).items():
            if opt not in c:
                raise ExportError("no switch %r; switches: %s" % (opt, sorted(k for k, e in c.items()
                                                                           if attr(e, "AXRole") == "AXButton")))
            el = c[opt]
            if (attr(el, "AXValue") == "On") != bool(want):
                AXUIElementPerformAction(el, "AXPress")
                wait_for(lambda: (attr(el, "AXValue") == "On") == bool(want), 3, opt)
            report["options"][opt] = attr(el, "AXValue")
        report["settings"] = {k: attr(e, "AXValue") for k, e in c.items()
                              if attr(e, "AXRole") in ("AXPopUpButton", "AXButton") and attr(e, "AXValue")}
    except Exception:
        if "Cancel" in c:
            AXUIElementPerformAction(c["Cancel"], "AXPress")
        raise
    # Export opens the save panel modally, so the press itself reports an error: ignore it and wait for the panel.
    AXUIElementSetMessagingTimeout(app, 0.5)
    AXUIElementPerformAction(c["Export"], "AXPress")
    AXUIElementSetMessagingTimeout(app, 3.0)
    save = wait_for(lambda: window(app, "Save"), 10, "the save panel")
    time.sleep(0.4)
    # The save panel runs in a separate macOS service: keystrokes (Go to Folder) don't reach it in the background,
    # and a typed path becomes part of the name. So save under a unique name in whatever folder the panel shows,
    # read that folder from Live's last-save-folder preference, and move the file to `out`.
    tmp = "faderhand-export-%d" % int(time.time() * 1000)
    nf = wait_for(lambda: next((e for e in _all(save, 6) if attr(e, "AXIdentifier") == "saveAsNameTextField"), None),
                  5, "the name field")
    AXUIElementSetAttributeValue(nf, "AXValue", tmp)
    time.sleep(0.2)
    if attr(nf, "AXValue") != tmp:
        raise ExportError("couldn't set the file name in the save panel")
    btn = next((e for e in _all(save, 6) if attr(e, "AXIdentifier") == "OKButton"), None)
    if btn is None:
        raise ExportError("no Save button in the save panel")
    shown = next((attr(e, "AXValue") for e in _all(save, 6) if attr(e, "AXIdentifier") == "where popup"), None)
    time.sleep(0.3)
    t0 = time.time()
    # A press that comes right after the name is set can be lost (2026-11-27, macOS 27: the panel stayed open with
    # Save enabled, and a second press closed it at once). So press again while the panel stays open; if it never
    # closes, cancel it and the Export window so Live isn't left behind a modal panel.
    for presses in range(1, 4):
        AXUIElementSetMessagingTimeout(app, 0.5)
        AXUIElementPerformAction(btn, "AXPress")
        AXUIElementSetMessagingTimeout(app, 3.0)
        try:
            wait_for(lambda: window(app, "Save") is None, 3.0, "the save panel to close")
            break
        except ExportError:
            if presses == 3:
                _cancel_open_panels(app, save)
                raise ExportError("the save panel didn't close after 3 presses of Save; cancelled it (nothing "
                                  "exported)")
    report["save_presses"] = presses
    ext = os.path.splitext(name)[1].lower()
    # A short render writes the file in the save folder straight away. A long one renders into a .aad in Live's
    # cache first and writes the file only at the end (found 2026-11-25 on a 31-minute export, which timed out
    # here after 60 s at about 60%). So keep waiting, up to `timeout`, while Live shows it is rendering.
    src = None
    while src is None:
        src = _find_tmp(tmp, ext, shown)
        if src:
            break
        waited = time.time() - t0
        if waited > timeout:
            raise ExportError("render didn't finish within %ss (no %s%s)" % (timeout, tmp, ext))
        if waited > 60 and not _rendering(app, t0):
            raise ExportError("timed out after 60s waiting for Live to start writing %s%s (no render window "
                              "and no render in Live's cache)" % (tmp, ext))
        time.sleep(0.5)
    last, still = -1, 0
    while time.time() - t0 < timeout:                         # rendered when the file stops growing for 3 s
        size = os.path.getsize(src)
        still = still + 1 if size == last and size > 0 else 0
        if still >= 6:
            break
        last = size
        time.sleep(0.5)
    else:
        raise ExportError("render didn't finish within %ss (%s)" % (timeout, src))
    os.rename(src, out) if os.stat(src).st_dev == os.stat(folder).st_dev else __import__("shutil").move(src, out)
    for side in (".asd",):                                    # an analysis file, if that option was on
        if os.path.exists(src + side):
            os.rename(src + side, out + side)
    report.update(file=out, bytes=os.path.getsize(out), seconds_to_export=round(time.time() - t0, 1))
    return report


def _cancel_open_panels(app, save):
    """Press Cancel in the save panel, then in the Export window if it is still open."""
    b = next((e for e in _all(save, 6) if attr(e, "AXIdentifier") == "CancelButton"), None)
    if b is not None:
        AXUIElementPerformAction(b, "AXPress")
        time.sleep(0.5)
    win = window(app, "Export Audio/Video")
    if win is not None:
        c = controls(win)
        if "Cancel" in c:
            AXUIElementPerformAction(c["Cancel"], "AXPress")


def _last_save_folder():
    from Foundation import CFPreferencesAppSynchronize, CFPreferencesCopyAppValue, NSURL
    CFPreferencesAppSynchronize(BUNDLE)
    d = CFPreferencesCopyAppValue("NSOSPLastRootDirectory", BUNDLE)
    if d is None:
        return None
    u, _stale, _err = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
        d, 0x100, None, None, None)
    return u.path() if u else None


def _find_tmp(tmp, ext, shown):
    folder = _last_save_folder()
    if folder and os.path.exists(os.path.join(folder, tmp + ext)):
        if shown and os.path.basename(folder) != shown:
            raise ExportError("save folder mismatch: panel showed %r, preference says %s" % (shown, folder))
        return os.path.join(folder, tmp + ext)
    return None


CACHE = os.path.expanduser("~/Library/Caches/Cleanup At Startup")


def _rendering(app, since):
    """Whether Live is still rendering: its "Rendering audio" progress window is open, or a render file (.aad) in
    its cache has grown since the export began."""
    for w in attr(app, "AXWindows") or []:
        if str(attr(w, "AXTitle") or "").lower().startswith("render"):
            return True
    try:
        for root, _dirs, files in os.walk(CACHE):
            for f in files:
                if f.endswith(".aad") and os.path.getmtime(os.path.join(root, f)) >= since - 1:
                    return True
    except OSError:
        pass
    return False


def _all(e, depth):
    yield e
    if depth:
        for k in kids(e):
            yield from _all(k, depth - 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="bar.beat.sixteenth, e.g. 9.1.1")
    ap.add_argument("--length", required=True, help="bars.beats.sixteenths, e.g. 8.0.0")
    ap.add_argument("--out", required=True, help="absolute path of the new file, e.g. /x/y/Song.wav")
    ap.add_argument("--option", action="append", default=[], help='"Normalize=off", "Render as Loop=on", ...')
    a = ap.parse_args()
    try:
        opts = {}
        for o in a.option:
            k, _, v = o.rpartition("=")
            opts[k] = v.strip().lower() in ("on", "1", "true", "yes")
        print(json.dumps({"ok": True, **export(a.start, a.length, a.out, opts)}))
    except ExportError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)
