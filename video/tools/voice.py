"""Speak the script with Kokoro and time every word.

    python3 tools/voice.py long|short

Audio comes from `npx hyperframes tts` (Kokoro-82M, local). Word timings come
from the same model's duration predictor (tools/kokoro_align.py); the two runs
are checked to be sample-identical, so the timings are exact, not estimated.
Pauses longer than a cap are shortened by cutting digital silence out of the
middle of them. Writes assets/voice/<id>.wav and script/<id>.timing.json.
"""
from __future__ import annotations
import difflib, hashlib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from kokoro_align import Aligner, SR  # noqa: E402

LEAD, LINE_GAP, SCENE_GAP, TAIL = 0.25, 0.10, 0.20, {"long": 2.4, "short": 2.4}
CAP = {",": 0.13, ";": 0.15, ":": 0.17, ".": 0.2, "?": 0.22, "!": 0.2}
PUNCT = set(",.;:!?")


def tighten(audio: np.ndarray, info: dict):
    """Cut silence out of long punctuation pauses. Returns audio and a time map."""
    ph, fr = info["phonemes"], info["frames"]
    edges = np.concatenate([[0], np.cumsum(fr)]) * info["hop"] / SR - info["lead"]
    cuts = []  # (start, end) seconds to remove, in trimmed-audio time
    for i, ch in enumerate(ph):
        if ch not in PUNCT or i >= len(ph) - 1:
            continue
        a, b = edges[i + 1], edges[i + 2]
        # include a following space token in the pause
        if i + 1 < len(ph) and ph[i + 1] == " ":
            b = edges[i + 3]
        extra = (b - a) - CAP[ch]
        if extra <= 0.03:
            continue
        mid = (a + b) / 2
        s, e = mid - extra / 2, mid + extra / 2
        seg = audio[int(s * SR):int(e * SR)]
        if len(seg) and float(np.sqrt(np.mean(seg ** 2))) < 0.012:   # only true silence
            cuts.append((s, e))
    out, pos = [], 0
    for s, e in cuts:
        out.append(audio[pos:int(s * SR)]); pos = int(e * SR)
    out.append(audio[pos:])
    fade = int(0.004 * SR)
    for k in range(1, len(out)):          # 4 ms fades each side of a splice
        if len(out[k - 1]) > fade and len(out[k]) > fade:
            out[k - 1][-fade:] *= np.linspace(1, 0, fade); out[k][:fade] *= np.linspace(0, 1, fade)

    def remap(t: float) -> float:
        return t - sum(min(max(t - s, 0), e - s) for s, e in cuts)
    return np.concatenate(out), remap, edges


def word_times(a: Aligner, say: str, info: dict, edges, remap, lang: str):
    """Start/end of each written word, by aligning per-word phonemes to the line's."""
    words = say.split()
    solo = [a.tok.phonemize(w, lang) for w in words]
    strip = lambda s: re.sub(r"[\sˈˌ,.;:!?]", "", s)
    A, owner = "", []
    for wi, s in enumerate(solo):
        s = strip(s) or "?"
        A += s; owner += [wi] * len(s)
    B, bidx = "", []
    for i, ch in enumerate(info["phonemes"]):
        if strip(ch):
            B += ch; bidx.append(i)
    t0, t1 = [None] * len(words), [None] * len(words)
    for blk in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            wi, pi = owner[blk.a + k], bidx[blk.b + k]
            s, e = remap(edges[pi + 1]), remap(edges[pi + 2])
            t0[wi] = s if t0[wi] is None else min(t0[wi], s)
            t1[wi] = e if t1[wi] is None else max(t1[wi], e)
    for i in range(len(words)):            # words with no match: borrow from neighbours
        if t0[i] is None:
            prev = next((t1[j] for j in range(i - 1, -1, -1) if t1[j] is not None), 0.0)
            t0[i] = t1[i] = prev
    return [{"w": w, "t0": round(float(s), 3), "t1": round(float(e), 3)} for w, s, e in zip(words, t0, t1)]


def main(vid: str) -> None:
    spec = json.loads((ROOT / f"script/{vid}.json").read_text())
    voice, speed = spec["voice"], spec["speed"]
    lang = "en-gb" if voice[0] == "b" else "en-us"
    raw = ROOT / "build/voice-raw"; raw.mkdir(parents=True, exist_ok=True)
    a = Aligner()
    t, track, scenes, nwords = LEAD, [np.zeros(int(LEAD * SR), dtype=np.float32)], [], 0
    for si, scene in enumerate(spec["scenes"]):
        sc = {"id": scene["id"], "lines": []}
        for li, line in enumerate(scene["lines"]):
            say = line.get("say", line["text"])
            key = hashlib.sha256(f"{voice}|{speed}|{say}".encode()).hexdigest()[:16]
            wav = raw / f"{key}.wav"
            if not wav.exists():
                subprocess.run(["npx", "hyperframes", "tts", say, "-v", voice, "-s", str(speed), "-o", str(wav)],
                               cwd=ROOT, check=True, capture_output=True)
            cli, sr = sf.read(str(wav), dtype="float32")
            audio, _, info = a.speak(say, voice, speed, lang)
            assert sr == SR and len(cli) == len(audio), f"CLI and aligner disagree on {say!r}"
            assert float(np.corrcoef(cli, audio)[0, 1]) > 0.999, f"waveforms differ on {say!r}"
            tight, remap, edges = tighten(cli.copy(), info)
            words = word_times(a, say, info, edges, remap, lang)
            for w in words:
                w["t0"] = round(w["t0"] + t, 3); w["t1"] = round(w["t1"] + t, 3)
            d = len(tight) / SR
            sc["lines"].append({"text": line["text"], "say": say, "start": round(t, 3), "end": round(t + d, 3), "words": words})
            nwords += len(line["text"].split())
            track.append(tight.astype(np.float32))
            last_line = li == len(scene["lines"]) - 1
            last_scene = si == len(spec["scenes"]) - 1
            gap = TAIL[vid] if (last_line and last_scene) else (SCENE_GAP + scene.get("hold", 0) if last_line else LINE_GAP)
            track.append(np.zeros(int(gap * SR), dtype=np.float32))
            t += d + gap
        scenes.append(sc)
    audio = np.concatenate(track)
    total = len(audio) / SR
    # scene windows: each scene starts 0.12 s before its first word; the first at 0
    for i, sc in enumerate(scenes):
        sc["start"] = 0.0 if i == 0 else round(sc["lines"][0]["start"] - 0.12, 3)
    for i, sc in enumerate(scenes):
        sc["end"] = round(scenes[i + 1]["start"] if i + 1 < len(scenes) else total, 3)
    (ROOT / "assets/voice").mkdir(parents=True, exist_ok=True)
    sf.write(str(ROOT / f"assets/voice/{vid}.wav"), audio, SR, subtype="PCM_16")
    (ROOT / f"script/{vid}.timing.json").write_text(json.dumps(
        {"id": vid, "voice": voice, "speed": speed, "total": round(total, 3), "scenes": scenes}, indent=1))
    speech = sum(l["end"] - l["start"] for s in scenes for l in s["lines"])
    print(f"{vid}: {nwords} words, {total:.1f}s total, {speech:.1f}s speech, "
          f"{nwords / total * 60:.0f} wpm overall, {nwords / speech * 60:.0f} wpm while speaking")
    for s in scenes:
        print(f"  {s['id']:8s} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end'] - s['start']:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1])
