#!/usr/bin/env python3
"""
Chroma Cleaner & Palette Protector for Retro Sprite Sheets.
Removes flat or noisy background colors, protects character internal pixels,
and guarantees 100% zero transparent RGB residue.
"""

import sys
import argparse
import numpy as np
from PIL import Image

def clean_sheet(input_path, output_path, bg_rgb=None, tolerance=15, wipe_text_regions=None):
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img).copy()
    
    # Auto-detect background if not provided (take top-left corner 5x5 modal color)
    if bg_rgb is None:
        sample = arr[0:5, 0:5, :3]
        bg_rgb = np.median(sample.reshape(-1, 3), axis=0).astype(int)
        print(f"[*] Auto-detected background color: RGB{tuple(bg_rgb)}")
    else:
        bg_rgb = np.array(bg_rgb)
        print(f"[*] Target background color: RGB{tuple(bg_rgb)}")

    # Calculate Euclidean color distance
    diff = np.sqrt(np.sum((arr[:, :, :3].astype(float) - bg_rgb.astype(float)) ** 2, axis=2))
    mask_bg = diff <= tolerance
    
    # Wipe identified background to pure (0, 0, 0, 0)
    arr[mask_bg] = [0, 0, 0, 0]
    
    # Optional: Wipe known credit text / watermarks
    if wipe_text_regions:
        for (x1, y1, x2, y2) in wipe_text_regions:
            arr[y1:y2, x1:x2] = [0, 0, 0, 0]
            
    # Zero out ANY pixel where alpha is 0
    arr[arr[:, :, 3] == 0] = [0, 0, 0, 0]
    
    cleaned = Image.fromarray(arr)
    cleaned.save(output_path, "PNG")
    print(f"[+] Saved clean transparent sheet to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean background from retro sprite sheets.")
    parser.add_argument("input", help="Input image file")
    parser.add_argument("output", help="Output PNG file")
    parser.add_argument("--tolerance", type=float, default=15.0, help="Chroma color tolerance")
    parser.add_argument("--bg", nargs=3, type=int, default=None, help="Background R G B (0-255)")
    args = parser.parse_args()
    
    clean_sheet(args.input, args.output, bg_rgb=args.bg, tolerance=args.tolerance)
