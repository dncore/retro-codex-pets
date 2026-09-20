#!/usr/bin/env python3
"""
Test Loop Generator for Retro Sprite Pet QA.
Renders candidate frame sequences to animated GIFs for visual inspection of loops,
seams, baseline alignment, and jitter.
"""

import sys
import argparse
from PIL import Image

def generate_preview_gif(frame_paths, output_gif, durations=100, scale=4, canvas_size=(192, 208)):
    frames = []
    if isinstance(durations, int):
        dur_list = [durations] * len(frame_paths)
    else:
        dur_list = durations

    for path in frame_paths:
        img = Image.open(path).convert("RGBA")
        bbox = img.getbbox()
        cropped = img.crop(bbox) if bbox else img
        sw = cropped.width * scale
        sh = cropped.height * scale
        scaled = cropped.resize((sw, sh), Image.NEAREST)
        
        c = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        # Default baseline y=186
        x = (canvas_size[0] - sw) // 2
        y = 186 - sh
        c.paste(scaled, (x, y), scaled)
        frames.append(c)

    frames[0].save(output_gif, save_all=True, append_images=frames[1:], duration=dur_list, loop=0)
    print(f"[+] Saved preview GIF to {output_gif}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate preview GIFs from frame images.")
    parser.add_argument("frames", nargs="+", help="Input frame image paths")
    parser.add_argument("--output", "-o", required=True, help="Output GIF path")
    parser.add_argument("--duration", "-d", type=int, default=100, help="Frame duration in ms")
    args = parser.parse_args()
    
    generate_preview_gif(args.frames, args.output, durations=args.duration)
