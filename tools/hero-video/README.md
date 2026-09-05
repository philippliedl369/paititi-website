# Home hero: animating the clouds

The home hero still (`assets/home/screenshot-2025-04-12-at-70237e280afpm.webp`)
is a 2500 × 1408 WebP, 66 KB — the old CDN's compressed copy, not a master.
That is fine for image-to-video: every tool downsamples to 1080p or lower
anyway, and the softness reads as haze.

## 1. Generate the clip (outside the repo)

Upload one of the frames in this folder to an image-to-video tool:

- **`home-hero-frame-4k.png`** — 3840 × 2160, deblocked and upscaled from the
  2500px still. Use this one: the platforms want ≥ 1080p, and the light
  denoise keeps the WebP blocking from turning into shimmer in the sky.
- `home-hero-frame.png` — the native 2500 × 1406 pixels, lossless, no
  processing, for tools that do their own upscale.

Both are exact 16:9. There is nothing better upstream: the Squarespace CDN
returns the same 66 KB WebP even for `?format=original`, and the upload itself
was a screenshot (`Screenshot 2025-04-12 at 7.02.37 PM.jpg`). If that
screenshot — or the photo it was taken of — still exists on someone's machine,
it beats both files here.

Any of these do a good job on skies:

| Tool | Notes |
|---|---|
| Runway Gen-3 / Gen-4 | best camera lock; "Image to Video", 10 s |
| Kling 2.x | strongest cloud physics, 10 s, choose "standard" motion |
| Luma Dream Machine | fast; use "loop" toggle if offered — saves step 2's dissolve |
| Google Veo 3 (Flow / Gemini) | 8 s, clean but tends to add camera drift |

Prompt (paste as-is, then trim to the tool's limit):

> Static locked-off camera, no camera movement, no zoom, no pan. Slow
> time-lapse of the clouds drifting gently from left to right and slowly
> billowing over the Andean mountain ridge at sunset. The mountains, the sun
> and the light rays stay completely still. Subtle, calm, cinematic,
> photorealistic, no new objects, no birds, no people, no text.

Negative prompt where available: `camera movement, zoom, pan, warping
mountains, flicker, morphing, text, watermark, people, birds`.

Settings that matter:

- **Duration:** the longest offered (10 s). The page loops it with a 1.5 s
  dissolve, so ≥ 8 s hides the join.
- **Motion strength:** low (Kling "standard", Runway motion 3–4 of 10). High
  values make the ridge line breathe, which is the one thing that gives the
  trick away.
- **Aspect:** 16:9, 1080p if the plan allows. Do not let the tool add sound.
- Generate three or four and pick the one where the **mountain silhouette does
  not move at all** — scrub the last second against the first.

## 2. Encode + loop

```bash
tools/hero_video.sh ~/Downloads/<the clip>.mp4
```

Writes `assets/video/home-hero.mp4` (1920 × 1080, H.264, silent, ~2–3 MB for
10 s at crf 24; `CRF=26` if you want it under 2 MB). The script dissolves the
tail into the head so the loop point is a slow cloud fade rather than a cut.

## 3. How the page uses it

Both `Home.dc.html` and `Home.es.dc.html` carry
`data-video="/assets/video/home-hero.mp4"` on the hero `<section>`, and
`/hero-video.js` (loaded from `<head>`) does the rest:

- The `<img>` still stays exactly as it is — it is the LCP image, the social
  card, the no-JS page, the reduced-motion page and the phone page.
- On a viewport ≥ 1181 px with `prefers-reduced-motion: no-preference` and
  no `saveData`, the script inserts a muted, looping, inline `<video>` behind
  the scrim and fades it in over the still once the first frame has decoded.
  Frame 0 of the clip *is* the still, so the hand-off is invisible.
- Phones never download it. It pauses while the hero is scrolled off-screen.
- If the file is missing or fails to decode, the video is removed and the still
  remains — which is what happens today, before the clip exists.

Nothing to regenerate: the still, its `srcset` and the head meta are untouched.
