"""Assemble a HyperFrames project from scenes/<video>/*.html and the voice timing.

    python3 tools/build.py long     -> index.html, compositions/*.html      (the detailed video)
    python3 tools/build.py short    -> short/index.html, short/compositions (the README video)

A scene file is plain HTML. Timing is written as the words being spoken:

    data-at="file list"        when "file list" starts in this scene's narration
    data-at="lock+0.2"         0.2 s after "lock" starts      data-at="run@2"  second "run"
    data-at="3.5"              absolute seconds from scene start;  "end-1" = before the scene ends
    data-out / data-dim / data-mt / data-ct take the same syntax.
    {{logo:python}}            inlines a Simple Icons logo.   {{T:phrase}} gives a number in <script>.

The build resolves each cue against script/<video>.timing.json and fails on any it
cannot find, so a reworded line can never leave a reveal behind.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1920, 1080
ATTRS = ("at", "out", "dim", "mt", "ct")
AMBIG: list[str] = []
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def resolver(scene: dict):
    words = [(norm(w["w"]), w["t0"] - scene["start"], w["t1"] - scene["start"]) for l in scene["lines"] for w in l["words"]]
    dur = scene["end"] - scene["start"]

    def cue(expr: str) -> float:
        expr = expr.strip()
        m = re.fullmatch(r"(.*?)\s*([+-]\s*\d*\.?\d+)?", expr)
        base, off = m.group(1).strip(), float((m.group(2) or "0").replace(" ", ""))
        if re.fullmatch(r"\d*\.?\d+", base):
            return round(float(base) + off, 3)
        if base == "end":
            return round(dur + off, 3)
        use_end = base.endswith(">")
        base = base.rstrip(">")
        nth = 1
        if "@" in base:
            base, n = base.rsplit("@", 1); nth = int(n)
        want = [norm(x) for x in base.split()]
        hits = [i for i in range(len(words) - len(want) + 1) if [w[0] for w in words[i:i + len(want)]] == want]
        if len(hits) < nth:
            raise SystemExit(f"[{scene['id']}] cue {expr!r} not found. Words: {' '.join(w[0] for w in words)}")
        if len(hits) > 1 and "@" not in expr:
            AMBIG.append(f"[{scene['id']}] {expr!r} matches {len(hits)}x at {[round(words[h][1], 1) for h in hits]} -> using the first")
        i = hits[nth - 1]
        return round((words[i + len(want) - 1][2] if use_end else words[i][1]) + off, 3)
    return cue, round(dur, 3)


def logo(name: str) -> str:
    svg = (ROOT / f"assets/logos/{name}.svg").read_text()
    return re.search(r"<svg.*</svg>", svg, re.S).group(0).replace("<svg ", '<svg fill="currentColor" ').replace("<title>", '<title data-x="').replace("</title>", '"></title>') if False else \
        re.sub(r"<title>.*?</title>", "", svg).replace("<svg ", '<svg fill="currentColor" ')


ICONS = {
    "lock": '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7.5a4 4 0 0 1 8 0V11"/></svg>',
    "check": '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13l5 5L20 6"/></svg>',
    "key": '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="4"/><path d="M11 12l8-8M16 7l3 3M14 9l2 2"/></svg>',
    "folder": '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
    "file": '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/></svg>',
}
NAT = {"dashboard-budget-and-rounds.png": 1920, "spawn.mp4": 1920, "stream.mp4": 1920, "merge.mp4": 1920}


def shot(arg: str) -> str:
    """{{shot:file|x|y|w|h|scale}} -> a cropped, scaled view of a real dashboard picture (inside a .shot)."""
    f, x, y, w, h, sc = arg.split("|")[:6]
    x, y, w, h, sc = float(x), float(y), float(w), float(h), float(sc)
    nat = NAT.get(f, 1600)
    return (f'<div class="win" data-layout-allow-overflow style="inset:auto;left:3px;top:3px;width:{w*sc:.0f}px;height:{h*sc:.0f}px">'
            f'<img src="assets/dashboard/{f}" alt="" style="width:{nat*sc:.0f}px;left:{-x*sc:.0f}px;top:{-y*sc:.0f}px"></div>')


def video(arg: str, cue) -> str:
    """{{video:id|file|x|y|w|h|scale|start-cue|duration|media-start}} -> a cropped, timed screen recording."""
    i, f, x, y, w, h, sc, st, du, ms = arg.split("|")
    x, y, w, h, sc = float(x), float(y), float(w), float(h), float(sc)
    nat = NAT.get(f, 1920)
    return (f'<div class="win" data-layout-allow-overflow style="inset:auto;left:3px;top:3px;width:{w*sc:.0f}px;height:{h*sc:.0f}px">'
            f'<video id="{i}" class="clip" muted playsinline preload="auto" src="assets/dashboard/{f}" data-start="{cue(st)}" data-duration="{du}" '
            f'data-media-start="{ms}" data-track-index="5" data-hf-media-start-basis="local" style="width:{nat*sc:.0f}px;height:{nat*sc*9/16:.0f}px;left:{-x*sc:.0f}px;top:{-y*sc:.0f}px"></video></div>')


def main(vid: str) -> None:
    timing = json.loads((ROOT / f"script/{vid}.timing.json").read_text())
    out = ROOT if vid == "long" else ROOT / vid
    (out / "compositions").mkdir(parents=True, exist_ok=True)
    if vid != "long" and not (out / "assets").exists():
        (out / "assets").symlink_to("../assets")
    shared = (ROOT / "scenes/shared.css").read_text()
    hosts = []
    for scene in timing["scenes"]:
        sid = scene["id"]
        src = (ROOT / f"scenes/{vid}/{sid}.html").read_text()
        cue, dur = resolver(scene)
        for a in ATTRS:
            src = re.sub(rf'data-{a}="([^"]*)"', lambda m, a=a: f'data-{"t" if a == "at" else a}="{cue(m.group(1))}"', src)
        src = re.sub(r"\{\{T:([^}]+)\}\}", lambda m: str(cue(m.group(1))), src)
        src = re.sub(r"\{\{logo:([a-z]+)\}\}", lambda m: logo(m.group(1)), src)
        src = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: ICONS[m.group(1)], src)
        src = re.sub(r"\{\{shot:([^}]+)\}\}", lambda m: shot(m.group(1)), src)
        src = re.sub(r"\{\{video:([^}]+)\}\}", lambda m: video(m.group(1), cue), src)
        src = src.replace("{{DUR}}", str(dur))
        style = "\n".join(re.findall(r"<style>(.*?)</style>", src, re.S))
        script = "\n".join(re.findall(r"<script>(.*?)</script>", src, re.S))
        markup = re.sub(r"<(style|script)>.*?</\1>", "", src, flags=re.S).strip()
        (out / "compositions" / f"{sid}.html").write_text(f"""<template>
  <style>
{shared}
{style}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <div class="scene" id="sc-{sid}">
{markup}
    </div>
  </div>
  <script>
    (async () => {{
      const scene = document.getElementById("sc-{sid}");
      const tl = gsap.timeline({{ paused: true }});
      const DUR = {dur};
      await EX.ready();
      EX.build(scene, tl, DUR);
{script}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
""")
        hosts.append(f'    <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{scene["start"]}" data-duration="{dur}" data-track-index="1" '
                     f'data-track-kind="graphics" data-width="{W}" data-height="{H}"></div>')
    total = timing["total"]
    music = ""
    if (ROOT / f"assets/music/{vid}-bed.wav").exists():
        music = (f'\n    <audio id="bed" class="clip" data-start="0" data-duration="{total}" data-track-index="3" '
                 f'data-volume="1" src="assets/music/{vid}-bed.wav"></audio>')
    (out / "index.html").write_text(f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Conductor{"" if vid == "long" else " (short)"}</title>
  <script src="assets/vendor/gsap.min.js"></script>
  <script src="assets/vendor/rough.js"></script>
  <script src="assets/ex.js"></script>
  <style>
    html, body {{ margin: 0; background: #121212; }}
    #main {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; background: #121212; }}
  </style>
</head>
<body>
  <div id="main" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
    <audio id="voice" class="clip" data-start="0" data-duration="{total}" data-track-index="2" data-volume="1" src="assets/voice/{vid}.wav"></audio>{music}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    window.__timelines["main"] = gsap.timeline({{ paused: true }});
  </script>
</body>
</html>
""")
    for a in AMBIG:
        print("  ambiguous cue", a)
    print(f"{vid}: {len(hosts)} scenes, {total:.1f}s -> {out.relative_to(ROOT.parent)}/index.html")


if __name__ == "__main__":
    main(sys.argv[1])
