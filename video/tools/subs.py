"""Burn captions into a finished video, in a band under the picture.

    python3 tools/subs.py short out/conductor-short-1.25x.mp4 out/conductor-short-1.25x-subs.mp4 --speed 1.25

Captions come from script/<id>.timing.json: each line's written text is split at
punctuation into chunks of at most MAXC characters, and each chunk is timed from
the spoken words it covers (written and spoken text differ for numbers, so the
chunk's position in the written line is mapped onto the spoken words by
proportion). --speed divides every time, for a video sped up after rendering.
The frame grows from 1920x1080 to 1920x1200 and the captions sit in the new
120 px band, so they never cover a scene. Needs .tmp/fonts/Excalifont-Regular.ttf
(converted from assets/fonts/Excalifont-Regular.woff2 with fontTools).
"""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAXC, BAND, FONT_PX = 58, 120, 44


def chunks(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"(?<=[,.:;])\s+", text) if p.strip()]
    merged: list[str] = []
    for p in parts:
        if merged and len(merged[-1]) + 1 + len(p) <= MAXC:
            merged[-1] += " " + p
        else:
            merged.append(p)
    out: list[str] = []
    for m in merged:
        while len(m) > MAXC:
            cut = m.rfind(" ", 0, len(m) // 2 + 8)
            cut = cut if cut > 0 else m.find(" ", len(m) // 2)
            out.append(m[:cut]); m = m[cut + 1:]
        out.append(m)
    return out


def ts(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def events(video: str, speed: float) -> list[tuple[float, float, str]]:
    timing = json.loads((ROOT / f"script/{video}.timing.json").read_text())
    ev = []
    for scene in timing["scenes"]:
        for line in scene["lines"]:
            words = line["words"]
            spoken = " ".join(w["w"] for w in words)
            spans, pos = [], 0
            for w in words:
                spans.append((pos, pos + len(w["w"]))); pos += len(w["w"]) + 1
            def at(frac: float) -> float:
                c = frac * len(spoken)
                for (a, b), w in zip(spans, words):
                    if c < b + 1:
                        return w["t0"]
                return words[-1]["t0"]
            text, pieces, start_c = line["text"], chunks(line["text"]), 0
            for i, piece in enumerate(pieces):
                c0 = text.find(piece, start_c); start_c = c0 + len(piece)
                t0 = at(c0 / len(text))
                t1 = at(start_c / len(text)) if i < len(pieces) - 1 else words[-1]["t1"] + 0.25
                ev.append((t0 / speed, t1 / speed, piece))
    # no overlaps: each caption ends where the next begins at the latest
    return [(a, min(b, ev[i + 1][0]) if i + 1 < len(ev) else b, s) for i, (a, b, s) in enumerate(ev)]


def ass(ev) -> str:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: {1080 + BAND}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Excalifont,{FONT_PX},&H00EFECE9,&H00EFECE9,&H00121212,&H00121212,0,0,0,0,100,100,0,0,1,0,0,2,40,40,{(BAND - FONT_PX) // 2 - 4},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + "".join(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{s}\n" for a, b, s in ev)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--speed", type=float, default=1.0)
    a = ap.parse_args()
    ev = events(a.video, a.speed)
    sub = ROOT / f".tmp/{a.video}-captions.ass"
    sub.parent.mkdir(exist_ok=True); sub.write_text(ass(ev))
    srt = Path(a.dst).with_suffix(".srt")
    st = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}".replace(".", ",")
    srt.write_text("".join(f"{i}\n{st(x)} --> {st(y)}\n{s}\n\n" for i, (x, y, s) in enumerate(ev, 1)))
    fonts = ROOT / ".tmp/fonts"
    vf = f"pad=1920:{1080 + BAND}:0:0:color=0x121212,subtitles={sub}:fontsdir={fonts}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-vf", vf, "-c:v", "libx264", "-crf", "16",
                    "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", a.dst], check=True)
    print(f"{len(ev)} captions -> {a.dst} (and {srt.name})")


if __name__ == "__main__":
    main()
