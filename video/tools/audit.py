"""Read-time audit: every on-screen line must stay up at least 0.5 s + 0.3 s per word.

    python3 tools/audit.py long|short

Reads the built compositions, takes each element that appears on a cue (data-t)
and measures from when it has finished appearing to when it leaves (data-out) or
its scene ends. Text that belongs to a child with its own cue is counted for that
child, not the parent. Code and JSON cards are judged on their highlighted words.
"""
import json, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.items = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        node = {"t": a.get("data-t"), "out": a.get("data-out"), "text": "", "cls": a.get("class", ""), "skip": tag in ("style", "script", "svg", "title")}
        self.stack.append(node)
        if tag in ("img", "br", "video"): self.stack.pop()
    def handle_endtag(self, tag):
        if tag in ("img", "br", "video") or not self.stack: return
        n = self.stack.pop()
        if n["t"] is not None: self.items.append(n)
        elif self.stack and not n["skip"]: self.stack[-1]["text"] += " " + n["text"]
    def handle_data(self, data):
        if self.stack and not any(s["skip"] for s in self.stack): self.stack[-1]["text"] += data


def main(vid):
    timing = json.loads((ROOT / f"script/{vid}.timing.json").read_text())
    base = ROOT if vid == "long" else ROOT / vid
    bad = total = 0
    for sc in timing["scenes"]:
        dur = sc["end"] - sc["start"]
        html = (base / "compositions" / f'{sc["id"]}.html').read_text()
        p = P(); p.feed(html)
        for n in p.items:
            words = [w for w in re.sub(r"\s+", " ", n["text"]).strip().split(" ") if re.search(r"[A-Za-z0-9]", w)]
            if not words or "term" in n["cls"]: continue
            total += 1
            shown = (float(n["out"]) if n["out"] else dur) - float(n["t"]) - 0.2
            need = 0.5 + 0.3 * len(words)
            if shown + 1e-6 < need:
                bad += 1
                print(f'  {sc["id"]:8s} {shown:5.2f}s < {need:4.1f}s  "{" ".join(words)[:70]}"')
    print(f"{vid}: {total} timed text elements, {bad} below 0.5 s + 0.3 s/word")

main(sys.argv[1])
