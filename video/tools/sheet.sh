#!/bin/sh
# tools/sheet.sh <cols> : tile the stills in .tmp/snap into .tmp/sheet.jpg (each 960 wide)
cd "$(dirname "$0")/.." && n=$(ls .tmp/snap/frame-*.png | wc -l) && rows=$(( (n + $1 - 1) / $1 )) && \
ffmpeg -v error -y -pattern_type glob -i ".tmp/snap/frame-*.png" -vf "scale=960:-1,tile=$1x$rows:padding=6:color=0x444444" -frames:v 1 -q:v 3 .tmp/sheet.jpg && echo "$n frames -> .tmp/sheet.jpg"
