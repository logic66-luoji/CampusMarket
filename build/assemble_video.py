# -*- coding: utf-8 -*-
"""Assemble presentation/video/CampusMarket-demo.mp4 + SRT from captured frames."""
from pathlib import Path
import imageio_ffmpeg
import subprocess

BASE = Path(r"D:\作业\master 1\5003\project\CampusMarket_Final")
SCALE = 1.4

manifest = [l for l in (BASE / "build" / "rec_manifest.log").read_text(encoding="utf-8").splitlines()
            if l.startswith("frame_")]
seen = {}
for l in manifest:
    seen[l.split("|")[0]] = l
items = []
for k in sorted(seen, key=lambda s: int(s.split("_")[1].split(".")[0])):
    f, cap, hold = seen[k].split("|")
    items.append((f, cap, round(int(hold) * SCALE * 2) / 2))

total = int(sum(h for _, _, h in items))
print(f"frames: {len(items)} | total: {total}s = {total // 60}:{total % 60:02d}")

concat = BASE / "build" / "concat.txt"
lines = []
for f, cap, hold in items:
    lines.append(f"file '../presentation/video/frames/{f}'")
    lines.append(f"duration {hold}")
lines.append(f"file '../presentation/video/frames/{items[-1][0]}'")
concat.write_text("\n".join(lines), encoding="utf-8")


def ts(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d},000"


srt_lines, t = [], 0.0
for i, (f, cap, hold) in enumerate(items, 1):
    srt_lines.append(f"{i}\n{ts(t)} --> {ts(t + hold - 0.5)}\n{cap}\n")
    t += hold
(BASE / "presentation" / "video" / "CampusMarket-demo.srt").write_text(
    "\n".join(srt_lines), encoding="utf-8")
print("SRT cues:", len(items))

out = BASE / "presentation" / "video" / "CampusMarket-demo.mp4"
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
       "-vf", "scale=1600:900,format=yuv420p", "-r", "30", "-c:v", "libx264",
       "-preset", "medium", "-crf", "23", "-movflags", "+faststart", str(out)]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if r.returncode != 0:
    print("FFMPEG STDERR tail:")
    print("\n".join(r.stderr.splitlines()[-8:]))
else:
    info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(out)],
                          capture_output=True, text=True)
    for line in info.stderr.splitlines():
        if "Duration" in line:
            print(line.strip())
    print("size MB:", round(out.stat().st_size / 1e6, 1))
    print("OK:", out.resolve())
