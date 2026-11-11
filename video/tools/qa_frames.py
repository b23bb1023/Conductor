"""Frame-level QA on a finished MP4.

    python3 tools/qa_frames.py long|short

1. Scans every frame for "nothing on screen" (how many pixels differ from the background).
2. Writes strips of real frames around the start, every scene cut and the end to .tmp/qa/.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
vid = sys.argv[1]
mp4 = ROOT / "out" / {"long": "conductor.mp4", "short": "conductor-short.mp4"}[vid]
timing = json.loads((ROOT / f"script/{vid}.timing.json").read_text())
W, H = 320, 180
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W)
ink = (np.abs(fr.astype(np.int16) - 18) > 14).mean(axis=(1, 2))      # share of pixels that are not background
print(f"{vid}: {len(fr)} frames, {len(fr) / 30:.2f}s")
empty = np.where(ink < 0.004)[0]
runs = []
for i in empty:
    if runs and i == runs[-1][1] + 1: runs[-1][1] = i
    else: runs.append([i, i])
print("frames with (almost) nothing on screen:", [(f"{a / 30:.2f}s", b - a + 1) for a, b in runs] or "none")
diff = np.abs(np.diff(fr.astype(np.int16), axis=0)).mean(axis=(1, 2))
still, start = [], 0
for i, d in enumerate(diff):
    if d > 0.02:
        if i - start > 90: still.append((start / 30, (i - start) / 30))
        start = i + 1
if len(diff) - start > 90: still.append((start / 30, (len(diff) - start) / 30))
print("stretches over 3.0 s with no change:", [(f"{a:.1f}s", f"{d:.1f}s") for a, d in still] or "none")
cuts = [s["start"] for s in timing["scenes"][1:]]
gaps = np.diff(np.where(diff > 0.02)[0]) / 30 if (diff > 0.02).any() else []
print(f"median gap between visible changes: {np.median(gaps):.2f}s, 90th percentile {np.percentile(gaps, 90):.2f}s")
out = ROOT / ".tmp/qa"; out.mkdir(parents=True, exist_ok=True)
def strip(name, frames):
    sel = "+".join(f"eq(n\\,{max(0, min(len(fr) - 1, f))})" for f in frames)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vf", f"select='{sel}',scale=480:270,tile={len(frames)}x1:padding=4:color=0x555555",
                    "-frames:v", "1", "-fps_mode", "vfr", str(out / name)], check=True)
strip(f"{vid}-start.png", list(range(0, 12, 2)))
strip(f"{vid}-end.png", [len(fr) - 1 - k for k in (40, 20, 8, 4, 1, 0)])
for i, c in enumerate(cuts):
    f = int(round(c * 30))
    strip(f"{vid}-cut{i + 1:02d}.png", [f - 3, f - 1, f, f + 1, f + 3, f + 9])
names = [f"{vid}-start.png"] + [f"{vid}-cut{i + 1:02d}.png" for i in range(len(cuts))] + [f"{vid}-end.png"]
for k in range(0, len(names), 6):
    part = names[k:k + 6]
    args = ["ffmpeg", "-v", "error", "-y"]
    for p in part: args += ["-i", str(out / p)]
    args += ["-filter_complex", f"vstack=inputs={len(part)}" if len(part) > 1 else "null", "-q:v", "3", str(out / f"{vid}-sheet{k // 6 + 1}.jpg")]
    subprocess.run(args, check=True)
    print("sheet", out / f"{vid}-sheet{k // 6 + 1}.jpg", part)
