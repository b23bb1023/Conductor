"""Kokoro with its duration predictor exposed, so every word gets a timestamp.

The Kokoro ONNX graph rounds and clips a per-token duration (in 25 ms frames)
before it expands the tokens into audio. That tensor is `/encoder/Clip_output_0`.
Adding it as a second graph output gives exact word timings for free, from the
same model run that makes the sound. No speech recogniser involved.

    from kokoro_align import Aligner
    a = Aligner()
    audio, words = a.speak("Up to eight run at once.", "am_michael", 1.2)
    # words: [{"w": "Up", "t0": 0.05, "t1": 0.21}, ...] in seconds of `audio`
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np

CACHE = Path.home() / ".cache/hyperframes/tts"
MODEL = CACHE / "models/kokoro-v1.0.onnx"
VOICES = CACHE / "voices/voices-v1.0.bin"
DUR_TENSOR = "/encoder/Clip_output_0"
SR = 24000

# `onnx` is only needed here, to add the extra output; it lives in .tmp/pylib.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".tmp/pylib"))


class Aligner:
    def __init__(self) -> None:
        import onnx
        import onnxruntime as rt
        from kokoro_onnx.tokenizer import Tokenizer
        from kokoro_onnx.trim import trim

        model = onnx.load(str(MODEL))
        model.graph.output.append(onnx.helper.make_empty_tensor_value_info(DUR_TENSOR))
        self.sess = rt.InferenceSession(model.SerializeToString(),
                                        providers=["CPUExecutionProvider"])
        del model
        self.voices = np.load(str(VOICES))
        self.tok = Tokenizer()
        self.trim = trim

    def speak(self, text: str, voice: str, speed: float, lang: str | None = None):
        lang = lang or ("en-gb" if voice[0] == "b" else "en-us")
        phonemes = self.tok.phonemize(text, lang)
        assert len(phonemes) <= 510, f"line too long for one Kokoro pass: {text!r}"
        ids = self.tok.tokenize(phonemes)
        style = self.voices[voice][len(ids)]
        audio, dur = self.sess.run(None, {
            "tokens": [[0, *ids, 0]],
            "style": style,
            "speed": np.ones(1, dtype=np.float32) * speed,
        })
        dur = np.asarray(dur).reshape(-1).astype(np.float64)
        hop = len(audio) / dur.sum()                      # samples per duration frame
        edges = np.concatenate([[0], np.cumsum(dur)]) * hop / SR   # token edges, seconds
        # kokoro-onnx trims leading/trailing silence; do the same and shift the clock.
        trimmed, idx = self.trim(audio)
        lead = idx[0] / SR
        # Token i of `ids` sits at edges[i + 1] (index 0 is the leading pad token).
        spans, cur, start = [], "", None
        for i, ch in enumerate(phonemes):
            t0, t1 = edges[i + 1] - lead, edges[i + 2] - lead
            if ch == " ":
                if cur:
                    spans.append((cur, start, end))
                cur, start = "", None
                continue
            if start is None:
                start = t0
            cur += ch
            end = t1
        if cur:
            spans.append((cur, start, end))
        # Drop phoneme "words" that are only punctuation.
        spans = [s for s in spans if re.search(r"[^\W_]", s[0], re.UNICODE)]
        total = len(trimmed) / SR
        words = [{"ph": p, "t0": round(max(0.0, a), 3), "t1": round(min(total, b), 3)}
                 for p, a, b in spans]
        return trimmed, words, {"hop": hop, "lead": lead, "frames": dur,
                                "phonemes": phonemes}
