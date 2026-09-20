#!/usr/bin/env python3
"""
Pet Doctor: Comprehensive Quality Assurance & Diagnostic Tool for Codex v2 Pets.
Checks:
1. Format & Dimensions (1536x2288)
2. Zero transparent RGB residue
3. Unused column purity (Rows 0, 3, 4, 6, 7, 8)
4. Edge Clipping & Truncation (flags pixels touching cell boundaries x=0, 191, y=0, 207)
5. Feet & Torso Drift across animations (detects jitter)
6. Anatomical integrity & neck/body tears (flags disconnected floating parts)
7. Run loop cadence & duplicate frame freezes
"""

import sys
import numpy as np
from PIL import Image

ROW_CONFIG = {
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

def diagnose_atlas(atlas_path):
    img = Image.open(atlas_path).convert("RGBA")
    w, h = img.size
    print(f"\n{'='*60}")
    print(f"  PET DOCTOR DIAGNOSTIC: {atlas_path}")
    print(f"{'='*60}")
    
    issues = []
    warnings = []
    
    # 1. Geometry
    if (w, h) != (1536, 2288):
        issues.append(f"Dimension error: Expected 1536x2288, got {w}x{h}")
    else:
        print("[✓] Geometry: 1536x2288 (11 rows x 8 cols, 192x208 cells)")
        
    arr = np.array(img)
    
    # 2. Transparent residue
    zero_alpha = arr[:, :, 3] == 0
    dirty = np.any(arr[:, :, :3][zero_alpha] > 0)
    if dirty:
        issues.append("Found non-zero RGB values in transparent alpha pixels")
    else:
        print("[✓] Zero-Residue Alpha: 100% clean")
        
    # 3. Unused column transparency
    for r in range(ROWS):
        name, _, unused = ROW_CONFIG[r]
        for c in unused:
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            if np.sum(cell[:, :, 3] > 0) > 0:
                issues.append(f"Row {r} ({name}) unused col {c} is not transparent")
    if not any("unused col" in s for s in issues):
        print("[✓] Unused Column Purity: 100% clean")

    # 4. Edge Clipping & Truncation
    clipping_found = False
    for r in range(ROWS):
        name, count, _ = ROW_CONFIG[r]
        for c in range(count):
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            if np.sum(cell[:, :, 3] > 0) == 0:
                continue
            # Allow projectile to exit right in Review (Row 8)
            t_top = np.sum(cell[0, :, 3] > 0)
            t_bot = np.sum(cell[207, :, 3] > 0)
            t_left = np.sum(cell[:, 0, 3] > 0)
            t_right = np.sum(cell[:, 191, 3] > 0)
            
            if r == 8 and (t_right > 0 and t_top == 0 and t_bot == 0 and t_left == 0):
                continue # projectile exiting right is allowed in Review
                
            if t_top > 0 or t_bot > 0 or t_left > 0 or (t_right > 0 and r != 8):
                clipping_found = True
                warnings.append(f"Edge clipping in Row {r:2d} ({name}) Col {c}: top={t_top}px, bot={t_bot}px, left={t_left}px, right={t_right}px")
                
    if not clipping_found:
        print("[✓] Boundary Clipping: 0 character pixels touching cell borders")
    else:
        print(f"[!] WARNING: Found {len(warnings)} boundary-clipped cells!")

    # 5. Stability & Centerline Jitter
    print("\n--- Centerline & Jitter Analysis ---")
    standing_feet_anchors = []
    for r in [0, 3, 6, 9, 10]:
        name, count, _ = ROW_CONFIG[r]
        f_centers = []
        for c in range(count):
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            ys, xs = np.where(cell[150:200, :, 3] > 0)
            if len(xs) > 0:
                f_centers.append(round((xs.min() + xs.max()) / 2.0, 1))
        if f_centers:
            drift = max(f_centers) - min(f_centers)
            status = "✓ Stable" if drift <= 2.0 else f"[!] Jitter ({drift}px drift)"
            print(f"Row {r:2d} ({name:18s}): feet={f_centers} -> {status}")
            standing_feet_anchors.extend(f_centers)
            if drift > 2.0:
                issues.append(f"Row {r} ({name}) feet jitter exceeds 2.0px (drift={drift}px)")
                
    # Check standing anchor consistency across Idle, Look, Waiting
    if standing_feet_anchors:
        global_drift = max(standing_feet_anchors) - min(standing_feet_anchors)
        if global_drift <= 2.0:
            print(f"[✓] Standing Base Consistency: 0.0~{global_drift}px across all standing states")
        else:
            warnings.append(f"Standing base shifts between states by {global_drift}px")

    # Running Head/Torso Jitter
    for r in [1, 2, 7]:
        name, count, _ = ROW_CONFIG[r]
        t_centers = []
        for c in range(count):
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            ys, xs = np.where(cell[:, :, 3] > 0)
            if len(ys) > 0:
                top_y, bot_y = ys.min(), ys.max()
                bh = bot_y - top_y
                head_y_limit = top_y + int(bh * 0.40)
                
                # Primary: face/skin landmark detection in head region (r - g >= 25 distinguishes skin from gold/yellow armor)
                head_cell = cell[:head_y_limit, :, :]
                r_c = head_cell[:, :, 0].astype(int)
                g_c = head_cell[:, :, 1].astype(int)
                b_c = head_cell[:, :, 2].astype(int)
                skin_mask = (head_cell[:, :, 3] > 0) & (r_c > 180) & (g_c > 130) & (b_c > 90) & (r_c - g_c >= 25) & (g_c > b_c)
                sk_ys, sk_xs = np.where(skin_mask)
                if len(sk_xs) > 0:
                    t_centers.append(round(float(sk_xs.mean()), 1))
                else:
                    hy1 = top_y + int(bh * 0.10)
                    hy2 = top_y + int(bh * 0.28)
                    hys, hxs = np.where(cell[hy1:hy2, :, 3] > 0)
                    if len(hxs) > 0:
                        t_centers.append(round(float((hxs.min() + hxs.max()) / 2.0), 1))
        if t_centers:
            drift = max(t_centers) - min(t_centers)
            status = "✓ Stable" if drift <= 2.0 else f"[!] Jitter ({drift:.1f}px drift)"
            print(f"Row {r:2d} ({name:18s}): head/crest={t_centers} -> {status}")
            if drift > 2.0:
                issues.append(f"Row {r} ({name}) head jitter exceeds 2.0px (drift={drift}px)")

    # 6. Run Cycle Cadence & Duplicate Frame Detection
    print("\n--- Run Cycle Cadence ---")
    for r in [1, 2, 7]:
        name, count, _ = ROW_CONFIG[r]
        duplicates = []
        for c in range(count):
            c_next = (c + 1) % count
            cell_a = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            cell_b = arr[r*CELL_H:(r+1)*CELL_H, c_next*CELL_W:(c_next+1)*CELL_W]
            diff = np.sum(np.abs(cell_a.astype(int) - cell_b.astype(int)))
            if diff == 0:
                duplicates.append((c, c_next))
        if duplicates:
            issues.append(f"Row {r} ({name}) has frozen duplicate frames: {duplicates}")
            print(f"[!] Row {r} ({name}): Frozen duplicate frames detected: {duplicates}")
        else:
            print(f"[✓] Row {r} ({name}): All {count} frames are unique, continuous cycle")

    # 7. Anatomical Tearing / Disconnect in Look Rows
    print("\n--- Anatomical Integrity (Tears & Disconnects) ---")
    tears = []
    for r in [9, 10]:
        name, count, _ = ROW_CONFIG[r]
        for c in range(count):
            cell = arr[r*CELL_H:(r+1)*CELL_H, c*CELL_W:(c+1)*CELL_W]
            # Check vertical continuity of character mask
            row_sums = np.sum(cell[:, :, 3] > 0, axis=1)
            active_ys = np.where(row_sums > 0)[0]
            if len(active_ys) > 0:
                y_min, y_max = active_ys[0], active_ys[-1]
                # Check for zero-alpha gap inside active character height
                interior = row_sums[y_min:y_max+1]
                zero_gaps = np.where(interior == 0)[0]
                if len(zero_gaps) > 0:
                    tears.append((r, c, len(zero_gaps)))
    if tears:
        issues.append(f"Severed head/neck tear detected in Look rows: {tears}")
        print(f"[!] Neck/body tears detected in Look rows: {tears}")
    else:
        print("[✓] Anatomical Integrity: 0 neck/body gaps, continuous character silhouette")

    print("\n" + "="*60)
    if not issues and not warnings:
        print("  RESULT: 100% HEALTHY (All checks passed!)")
        print("="*60 + "\n")
        return True
    else:
        print(f"  RESULT: {len(issues)} ERRORS, {len(warnings)} WARNINGS")
        for i in issues:
            print(f"   [ERROR]   {i}")
        for w in warnings:
            print(f"   [WARNING] {w}")
        print("="*60 + "\n")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pet_doctor.py <path_to_spritesheet.webp_or_png>")
        sys.exit(1)
    success = diagnose_atlas(sys.argv[1])
    sys.exit(0 if success else 1)
