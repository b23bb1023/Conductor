"""Mix the voice with a quiet music bed, level it, and mux it onto the render.

    python3 tools/mix.py long|short [--no-music]

Voice: assets/voice/<id>.wav (Kokoro, 24 kHz mono). Bed: one CC0 track, its quiet
intro skipped, looped with a 4 s crossfade, band-limited and dipped around 2.5 kHz
so it stays out of the voice's way. The bed is ducked from the script's own timing
(script/<id>.timing.json): 8 dB down while a line is spoken, back up in the pauses
and under the end card. The mix is set to -16 LUFS and limited to -2 dBTP before
AAC; the result is measured again from the final MP4.
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
TRACK = ROOT / "assets/music/HoliznaCC0 - Windows Down.mp3"
BODY = {"long": [(10.0, 158.0), (12.0, 112.0)], "short": [(60.0, 104.0), (12.0, 42.0)]}   # seconds of the track used
BED_LUFS, DUCK_DB, TARGET, LIMIT_DB = -30.0, -8.0, -16.0, -2.0
OUT = {"long": "conductor.mp4", "short": "conductor-short.mp4"}


def ff(*a: str) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *a], capture_output=True, text=True, check=True).stderr


def loudness(path: Path) -> dict:
    e = ff("-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-")
    tail = e[e.rindex("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+)", tail).group(1))
    return {"I": g("I"), "LRA": g("LRA"), "TP": g("Peak")}


def main(vid: str, music: bool) -> None:
    timing = json.loads((ROOT / f"script/{vid}.timing.json").read_text())
    total = timing["total"]
    work = ROOT / "build/audio"; work.mkdir(parents=True, exist_ok=True)
    voice48 = work / f"{vid}-voice48.wav"
    ff("-i", str(ROOT / f"assets/voice/{vid}.wav"), "-af", f"highpass=f=70,aresample={SR}:resampler=soxr", "-ac", "2", str(voice48))
    v, _ = sf.read(str(voice48), dtype="float32")
    n = int(round(total * SR))
    v = np.pad(v, ((0, max(0, n - len(v))), (0, 0)))[:n]
    v *= 10 ** ((TARGET - 0.3 - loudness(voice48)["I"]) / 20)
    mix = v.copy()
    if music:
        segs = BODY[vid]
        eq = "highpass=f=60,lowpass=f=7000,equalizer=f=2500:t=q:w=0.8:g=-4"
        if len(segs) == 1:
            graph = f"[0:a]atrim={segs[0][0]}:{segs[0][1]},asetpts=PTS-STARTPTS,{eq}[o]"
        else:
            graph = (f"[0:a]atrim={segs[0][0]}:{segs[0][1]},asetpts=PTS-STARTPTS[a];"
                     f"[0:a]atrim={segs[1][0]}:{segs[1][1]},asetpts=PTS-STARTPTS[b];[a][b]acrossfade=d=4:c1=tri:c2=tri,{eq}[o]")
        bedraw = work / f"{vid}-bed-raw.wav"
        ff("-i", str(TRACK), "-filter_complex", graph, "-map", "[o]", "-ar", str(SR), "-ac", "2", str(bedraw))
        b, _ = sf.read(str(bedraw), dtype="float32")
        assert len(b) >= n, f"bed too short: {len(b) / SR:.1f}s < {total:.1f}s"
        b = b[:n] * 10 ** ((BED_LUFS - loudness(bedraw)["I"]) / 20)
        # duck from the script's timing: down while a line is spoken, up in pauses of 0.45 s or more
        env = np.zeros(n, dtype=np.float32)
        lines = [(l["start"], l["end"]) for s in timing["scenes"] for l in s["lines"]]
        merged = [list(lines[0])]
        for a, z in lines[1:]:
            if a - merged[-1][1] < 0.45: merged[-1][1] = z
            else: merged.append([a, z])
        for a, z in merged:
            env[max(0, int((a - 0.10) * SR)):min(n, int((z + 0.05) * SR))] = DUCK_DB
        k = int(0.30 * SR); kern = np.hanning(k); kern /= kern.sum()
        env = np.convolve(env, kern, mode="same")
        b *= (10 ** (env / 20))[:, None]
        fi, fo = int(0.35 * SR), int(1.8 * SR)
        b[:fi] *= np.linspace(0, 1, fi)[:, None]; b[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
        sf.write(str(work / f"{vid}-bed.wav"), b, SR, subtype="PCM_24")
        mix = v + b
    pre = work / f"{vid}-premix.wav"; sf.write(str(pre), mix, SR, subtype="PCM_24")
    gain = TARGET - loudness(pre)["I"]
    final = work / f"{vid}-mix.wav"
    # static gain, then a true-peak-safe limiter (4x oversampled)
    ff("-i", str(pre), "-af", f"volume={gain:.2f}dB,aresample=192000:resampler=soxr,alimiter=limit={10 ** (LIMIT_DB / 20):.4f}:level=false:attack=3:release=60,aresample={SR}:resampler=soxr",
       "-c:a", "pcm_s24le", str(final))
    (ROOT / "out").mkdir(exist_ok=True)
    out = ROOT / "out" / OUT[vid]
    ff("-i", str(ROOT / f"renders/{vid}-raw.mp4"), "-i", str(final), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out))
    m = loudness(out)
    rep = {"video": vid, "file": out.name, "music": music, "integrated_LUFS": m["I"], "LRA": m["LRA"], "true_peak_dBTP": m["TP"]}
    if music:
        rep["bed_under_speech_LUFS"] = round(BED_LUFS + DUCK_DB + gain, 1)
        rep["bed_in_pauses_LUFS"] = round(BED_LUFS + gain, 1)
    (work / f"{vid}-loudness.json").write_text(json.dumps(rep, indent=1))
    print(rep)


if __name__ == "__main__":
    main(sys.argv[1], "--no-music" not in sys.argv)
