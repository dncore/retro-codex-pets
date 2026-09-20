#!/usr/bin/env python3
"""
Diagnostic and Quality Assurance Script for Codex v2 Pet Atlases.
Checks:
1. Geometry & dimensions (1536x2288)
2. Unused column transparency (Row 3, 4, 6, 7, 8)
3. Zero-residue alpha validation (RGB == 0 where A == 0)
4. Feet & Torso centerline stability across animation frames (Detects jitter)
"""

import sys
import numpy as np
from PIL import Image

ROW_RULES = {
    0: ("idle", 6, [7]),
    1: ("running-right", 8, []),
    2: ("running-left", 8, []),
    3: ("waving", 4, [4, 5, 6, 7]),
    4: ("jumping", 5, [5, 6, 7]),
    5: ("failed", 8, []),
    6: ("waiting", 6, [6, 7]),
    7: ("running", 6, [6, 7]),
    8: ("review", 6, [6, 7]),
    9: ("look-000-to-157.5", 8, []),
    10: ("look-180-to-337.5", 8, []),
}

CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 11

def inspect_atlas(atlas_path):
    img = Image.open(atlas_path).convert("RGBA")
    w, h = img.size
    print(f"=== Inspecting Atlas: {atlas_path} ===")
    print(f"Dimensions: {w}x{h} (Expected: 1536x2288)")
    if (w, h) != (1536, 2288):
        print(f"[!] ERROR: Atlas size {w}x{h} does not match Codex v2 1536x2288!")
        return False
        
    arr = np.array(img)
    
    # Check zero-residue alpha
    zero_alpha = arr[:, :, 3] == 0
    dirty_rgb = np.any(arr[:, :, :3][zero_alpha] > 0)
    if dirty_rgb:
        count = np.sum(np.any(arr[:, :, :3][zero_alpha] > 0, axis=1))
        print(f"[!] WARNING: Found {count} transparent pixels with non-zero RGB residue!")
    else:
        print("[✓] Zero-residue alpha: 100% clean (0 transparent RGB residue)")

    # Check each row
    all_ok = True
    for r in range(ROWS):
        state_name, frame_count, unused_cols = ROW_RULES[r]
        feet_centers = []
        
        # Check unused columns
        for c in unused_cols:
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            non_trans = np.sum(cell[:, :, 3] > 0)
            if non_trans > 0:
                print(f"[!] ERROR: {state_name} (Row {r}) unused column {c} has {non_trans} non-transparent pixels!")
                all_ok = False
                
        # Check active frames
        for c in range(frame_count):
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            if "running" in state_name:
                # Check torso center (y=80..130) for running
                ys, xs = np.where(cell[80:130, :, 3] > 0)
            else:
                # Check feet center for standing/action
                ys, xs = np.where(cell[160:190, :, 3] > 0)
                
            if len(xs) > 0:
                fc = (xs.min() + xs.max()) / 2.0
                feet_centers.append(round(fc, 1))
            else:
                feet_centers.append(None)
                
        # Report jitter
        valid_fc = [fc for fc in feet_centers if fc is not None]
        metric = "Torso" if "running" in state_name else "Feet"
        if len(valid_fc) > 1:
            drift = max(valid_fc) - min(valid_fc)
            status = "✓ Stable" if drift <= 6.0 else f"[!] Jitter ({drift}px drift)"
            print(f"Row {r:2d} ({state_name:18s}): {valid_fc} -> {metric} {status}")
        else:
            print(f"Row {r:2d} ({state_name:18s}): {valid_fc}")
            
    return all_ok

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_pet.py <path_to_spritesheet.webp_or_png>")
        sys.exit(1)
    inspect_atlas(sys.argv[1])
