#!/usr/bin/env python3
"""Render an animated preview GIF for each pet package in pets/.

The track table below mirrors agent-pet-runtime's CompatibilityProfile
(openAICodexV2): same rows, same frame counts, same authored per-frame
durations. Playback shape follows the runtime too — one-shot moments play
their row more than once so a glance does not miss them, locomotion rows
loop, and the sixteen gaze poses are shown as a sweep.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CELL_W, CELL_H = 192, 208           # V2 atlas cell
BAND = 36                           # caption band above the stage, 1x units
STAGE_H = 232                       # sprite stage, 1x units
CANVAS_W = 320                      # room for the run travel, 1x units
CELL_X = (CANVAS_W - CELL_W) // 2
CELL_Y = BAND + 12
TRAVEL = 32                         # px the pet runs from / back to centre, 1x

# name -> (row, per-frame durations in seconds)
TRACKS = {
    "idle":          (0, [0.280, 0.110, 0.110, 0.140, 0.140, 0.320]),
    "running-right": (1, [0.120] * 7 + [0.220]),
    "running-left":  (2, [0.120] * 7 + [0.220]),
    "waving":        (3, [0.140] * 3 + [0.280]),
    "jumping":       (4, [0.140] * 4 + [0.280]),
    "failed":        (5, [0.140] * 7 + [0.240]),
    "waiting":       (6, [0.150] * 5 + [0.260]),
    "running":       (7, [0.120] * 5 + [0.220]),
    "review":        (8, [0.150] * 5 + [0.280]),
}
LOOK_ROWS = (9, 10)                 # 16 gaze poses, clockwise from up
LOOK_SECONDS = 0.10

# (track, passes, caption, travel) — travel is "right" / "left" / None
SEQUENCE = [
    ("idle", 1, "idle", None),
    ("running-right", 1, "running right", "right"),
    ("running-left", 1, "running left", "left"),
    ("waving", 2, "waving", None),
    ("jumping", 2, "jumping", None),
    ("waiting", 1, "waiting", None),
    ("failed", 1, "failed", None),
    ("running", 1, "working", None),
    ("review", 2, "review", None),
    ("look", 1, "looking around", None),
]

THEMES = {
    # caption band, stage, checker pair (None = flat stage)
    "checker": ((22, 24, 29), (247, 248, 250), ((236, 238, 242))),
    "paper":   ((22, 24, 29), (247, 248, 250), None),
    "ink":     ((16, 17, 21), (24, 26, 32), None),
}


def load_font(size):
    for path, index in (
        ("/System/Library/Fonts/Menlo.ttc", 1),          # bold
        ("/System/Library/Fonts/Menlo.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
        ("/Library/Fonts/Arial.ttf", 0),
    ):
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    return ImageFont.load_default()


def stage(theme, scale):
    band_rgb, fill_rgb, checker_rgb = THEMES[theme]
    w, h = CANVAS_W * scale, (BAND + STAGE_H) * scale
    img = Image.new("RGB", (w, h), fill_rgb)
    if checker_rgb:
        draw = ImageDraw.Draw(img)
        step = 16 * scale
        for y in range(BAND * scale, h, step):
            for x in range(0, w, step):
                if ((x // step) + (y // step)) % 2:
                    draw.rectangle([x, y, x + step - 1, y + step - 1], fill=checker_rgb)
    ImageDraw.Draw(img).rectangle([0, 0, w, BAND * scale - 1], fill=band_rgb)
    return img


def caption(img, name, action, scale, fonts):
    draw = ImageDraw.Draw(img)
    pad = 12 * scale
    mid = BAND * scale // 2
    name_font, action_font = fonts
    draw.text((pad, mid), name, font=name_font, fill=(242, 244, 248), anchor="lm")
    draw.text((img.width - pad, mid), action, font=action_font, fill=(158, 176, 200), anchor="rm")


def build_frames(sheet, display_name, scale, theme, fonts):
    frames, durations = [], []
    for track, passes, label, travel in SEQUENCE:
        if track == "look":
            cells = [(r, c) for r in LOOK_ROWS for c in range(8)]
            durations_row = [LOOK_SECONDS] * len(cells)
        else:
            row, durations_row = TRACKS[track]
            cells = [(row, c) for c in range(len(durations_row))]
        n = len(cells)
        for _ in range(passes):
            for k, ((r, c), dur) in enumerate(zip(cells, durations_row)):
                # Travel is indexed, not timed, so the outgoing row lands exactly
                # on the right edge and the return row lands exactly on centre:
                # the two rows join without a step and the next track starts
                # centred.
                offset = 0
                if travel == "right":
                    offset = TRAVEL * (k / (n - 1))             # centre -> right edge
                elif travel == "left":
                    offset = TRAVEL * ((n - 1 - k) / (n - 1))   # right edge -> centre
                offset = int(round(float(offset)))
                img = stage(theme, scale)
                cell = sheet.crop((c * CELL_W, r * CELL_H, (c + 1) * CELL_W, (r + 1) * CELL_H))
                cell = cell.resize((CELL_W * scale, CELL_H * scale), Image.NEAREST)
                pos = ((CELL_X + offset) * scale, CELL_Y * scale)
                img.paste(cell, pos, cell)
                caption(img, display_name, label, scale, fonts)
                frames.append(img)
                durations.append(int(round(dur * 1000)))
    return frames, durations


def to_gif_palette(frames):
    """One palette for the whole sequence, so nothing shifts between frames."""
    colors = set()
    for img in frames:
        colors.update(map(tuple, np.unique(np.asarray(img).reshape(-1, 3), axis=0)))
    flat = Image.new("RGB", (len(colors), 1))
    flat.putdata(sorted(colors))
    palette = flat.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    return [img.quantize(palette=palette, dither=Image.Dither.NONE) for img in frames]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pets-dir", default=Path(__file__).resolve().parent.parent / "pets", type=Path)
    ap.add_argument("--out-dir", default=Path(__file__).resolve().parent.parent / "previews", type=Path)
    ap.add_argument("--pets", nargs="*", help="pet ids (default: every package found)")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--background", choices=sorted(THEMES), default="checker")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    fonts = (load_font(13 * args.scale), load_font(12 * args.scale))
    ids = args.pets or sorted(p.name for p in args.pets_dir.iterdir() if (p / "pet.json").exists())
    if not ids:
        sys.exit(f"no pet packages under {args.pets_dir}")

    for pet_id in ids:
        manifest = json.loads((args.pets_dir / pet_id / "pet.json").read_text())
        sheet = Image.open(args.pets_dir / pet_id / manifest.get("spritesheetPath", "spritesheet.webp")).convert("RGBA")
        frames, durations = build_frames(sheet, manifest.get("displayName", pet_id), args.scale, args.background, fonts)
        out = args.out_dir / f"{pet_id}.gif"
        palette_frames = to_gif_palette(frames)
        palette_frames[0].save(
            out, save_all=True, append_images=palette_frames[1:],
            duration=durations, loop=0, optimize=True,
        )
        total = sum(durations) / 1000
        print(f"{out}  {len(frames)} frames, {total:.1f}s, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
