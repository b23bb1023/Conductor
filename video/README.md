# The video

`media/conductor-short.mp4` (0:55) is built from this folder. It is made of HTML scenes in an Excalidraw style (rough.js shapes, Excalifont), animated with GSAP and rendered to MP4 with [HyperFrames](https://github.com/heygen-com/hyperframes). The voice is Kokoro, a local text-to-speech model, and every reveal is timed to the word that names it.

## Layout

| Path | What |
|---|---|
| `script/short.json` | The narration: what each line says on screen and, where a name needs help, how to say it |
| `script/*.timing.json` | Every spoken word with its start and end time, written by `tools/voice.py` |
| `scenes/short/` | One HTML file per scene. `data-at="file list"` reveals an element when those words are spoken |
| `scenes/shared.css`, `assets/ex.js` | The look, and the engine that draws rough.js outlines and turns cues into tweens |
| `assets/dashboard/` | Real Conductor dashboard screenshots and recordings, private text blurred |
| `assets/music/` | The CC0 music bed |
| `SCRIPT.md` | Narration and shot list |
| `CREDITS.md` | Music, voice, fonts, libraries and logos, with licenses |

## Rebuilding

Needs Node 22, ffmpeg with libass, Python 3 with `kokoro-onnx`, `soundfile` and `numpy`, and a Chrome build for HyperFrames.

```sh
npm install
pip install --target .tmp/pylib onnx fonttools brotli   # word timing, and the caption font
python3 tools/voice.py short        # speak and time every word
python3 tools/build.py short        # scenes + timing -> the HyperFrames project in short/
python3 tools/audit.py short        # every label stays up long enough to read
npx hyperframes check short
npx hyperframes render short -o renders/short-raw.mp4 -q delivery -f 30
python3 tools/mix.py short          # music bed, ducking, -16 LUFS -> out/conductor-short.mp4
```

The short video is then sped up 1.25x as a whole and captioned:

```sh
ffmpeg -i out/conductor-short.mp4 -filter_complex \
  "[0:v]setpts=PTS/1.25,fps=30[v];[0:a]atempo=1.25,loudnorm=I=-16:TP=-1.5:LRA=7[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 16 -c:a aac -b:a 192k out/conductor-short-1.25x.mp4
PYTHONPATH=.tmp/pylib python3 -c "from fontTools.ttLib import TTFont; f=TTFont('assets/fonts/Excalifont-Regular.woff2'); f.flavor=None; import os; os.makedirs('.tmp/fonts', exist_ok=True); f.save('.tmp/fonts/Excalifont-Regular.ttf')"
python3 tools/subs.py short out/conductor-short-1.25x.mp4 out/conductor-short-subs.mp4 --speed 1.25
```

Captions sit in a 120 px band added under the picture, so the final frame is 1920x1200 and a caption never covers a scene.
