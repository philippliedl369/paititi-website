#!/usr/bin/env bash
# Turn an AI-generated clip of the home hero into the file the page plays.
#
#   tools/hero_video.sh ~/Downloads/runway-clouds.mp4
#
# Input : whatever the image-to-video tool exported (any size, any codec, with
#         or without audio). Make it from tools/hero-video/home-hero-frame.png
#         so frame 0 matches the still the page already shows — see
#         tools/hero-video/README.md for the prompt and settings.
# Output: assets/video/home-hero.mp4 — 1920x1080, H.264 yuv420p, silent,
#         faststart, and looped seamlessly: the last $XFADE seconds dissolve
#         into the first $XFADE seconds, so the join is a slow cloud dissolve
#         instead of a jump cut. Home.dc.html / Home.es.dc.html point at it
#         through data-video on the hero section; nothing else to wire.
#
# Then: serve it (npm start), look at / at 1440px and on a phone, git push,
# npx wrangler deploy.
set -euo pipefail

IN="${1:?usage: tools/hero_video.sh <clip from the AI tool>}"
OUT="${2:-assets/video/home-hero.mp4}"
XFADE="${XFADE:-1.5}"   # seconds of dissolve at the loop point
CRF="${CRF:-24}"        # 22 = bigger/sharper, 26 = smaller/softer

cd "$(dirname "$0")/.."
mkdir -p "$(dirname "$OUT")"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
OFFSET=$(python3 -c "print(max(0.0, $DUR - 2*$XFADE))")

# [main] = clip minus its first XFADE seconds; [head] = those first XFADE
# seconds. Dissolving main's tail into head lands the final frame on the
# frame main starts on, so play→loop→play is continuous.
ffmpeg -v error -y -i "$IN" -an -filter_complex "
  [0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,setsar=1,split[a][b];
  [a]trim=start=$XFADE,setpts=PTS-STARTPTS[main];
  [b]trim=duration=$XFADE,setpts=PTS-STARTPTS[head];
  [main][head]xfade=transition=fade:duration=$XFADE:offset=$OFFSET,format=yuv420p[v]
" -map "[v]" -c:v libx264 -preset slow -crf "$CRF" -profile:v high -level 4.0 \
  -movflags +faststart -pix_fmt yuv420p "$OUT"

ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration,bit_rate -of default=nw=1 "$OUT"
ls -la "$OUT"
echo "ok → $OUT"
