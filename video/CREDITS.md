# Credits and licenses

Everything in the video is listed here with its license and where the license was checked.

## Music

"Windows Down" by HoliznaCC0. License CC0 1.0 Universal, so no attribution is required. It is credited here anyway.

- File used: `freemusicarchive.org/HoliznaCC0 - Windows Down.mp3` from the GitHub repository `SoundSafari/CC0-1.0-Music`, a collection of CC0 music gathered from Free Music Archive, FreePD, Chosic and others.
- What was checked: the repository's `LICENSE` file is the CC0 1.0 legal code, and its README says the collection holds only public-domain or CC0 music and takes takedown requests.
- What was not checked: the track's own page on Free Music Archive. That host is blocked from the build sandbox. The artist publishes under the name HoliznaCC0 and releases his catalogue as CC0, but confirm the track page before relying on this for anything beyond these videos.
- How it is used: seconds 60 to 104, then 12 to 42 of the track, joined with a 4 second crossfade. Band-limited to 60 Hz to 7 kHz with a 4 dB dip at 2.5 kHz, and turned down 8 dB while a line is spoken.

## Voice

Kokoro-82M, voice `af_heart`, speed 1.3, generated locally with `npx hyperframes tts`. The short video is then sped up 1.25x as a whole (picture and sound, pitch kept). Model license Apache-2.0 (checked in `hexgrad/kokoro`). Run through `kokoro-onnx`, MIT (checked in `thewh1teagle/kokoro-onnx`). The phonemizer behind it is espeak-ng, GPL-3.0, used as a tool and not distributed here.

## Fonts

| Font | Used for | License | Checked in |
|---|---|---|---|
| Excalifont Regular | all hand-drawn text | SIL Open Font License 1.1 | the font metadata in `excalidraw/excalidraw`, `packages/excalidraw/fonts/Excalifont` |
| Comic Shanns Regular 1.3.0 | code, commands, JSON | MIT | the font's own name table and `shannpersand/comic-shanns` |

Both files come from the npm package `@excalidraw/excalidraw` 0.18.1 (MIT) and sit in `assets/fonts/`. Only the Latin subset of Excalifont is shipped.

## Libraries

| Library | Version | License | Note |
|---|---|---|---|
| HyperFrames | 0.9.33 | Apache-2.0 | renders the HTML scenes to video |
| GSAP | 3.15.0 | GreenSock standard license, free to use, not open source | the copy bundled with HyperFrames |
| rough.js | 4.6.6 | MIT | draws the sketchy outlines. The vendored copy in `assets/vendor/rough.js` has one change, described in its header. Every `Math.random()` fallback is replaced by a fixed-seed generator so two renders can never differ |
| ffmpeg | 8 | LGPL/GPL | muxing, loudness measurement, frame extraction. Used as a tool |

`onnx` (Apache-2.0) was installed from PyPI into a scratch folder to read word timings out of the Kokoro model. It is a build tool and is not part of the videos.

## Logos

From Simple Icons 16.37.0. The icon set is CC0 1.0. Each mark is a trademark of its owner and is used here only to name the product it belongs to.

| Logo | Where | Note |
|---|---|---|
| opencode | free-model pills, worker rows | |
| OpenRouter | GLM and DeepSeek rows | |
| Google Gemini | Gemini row | |
| Claude | the Opus manager | |
| Model Context Protocol | the MCP arrow | |
| Python | the Conductor box | Python Software Foundation trademark |
| Git | worktrees, commits | Git Logo by Jason Long, CC BY 3.0 |
| GitHub | the repo card | |

OpenAI has no logo in Simple Icons, so the GPT rows use plain text. Space Bunny, Muse Spark, Fledge Alpha and the other model names are plain text for the same reason.

## Dashboard pictures and recordings

The screenshots and the three screen recordings in `assets/dashboard/` are the operator's own captures of the Conductor dashboard, supplied with private text already blurred. They are cropped, scaled and annotated. Nothing was un-blurred and no new footage was captured.

## Style reference

The look follows two videos by Arjay McCandless, studied for pacing and layout only. No frames, audio or assets from them are used.
