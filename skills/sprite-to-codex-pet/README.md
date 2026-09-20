# sprite-to-codex-pet

An agent skill that turns a sprite sheet from anywhere — a console game rip, a MUGEN pack, your own pixel art — into a compliant Codex v2 desktop pet. It is the skill the [four pets in this repository](../../README.md) were built with.

The skill's own instructions are written in Chinese; the frontmatter description is English so agents can match on it.

## What it does

It steers an agent away from the obvious wrong move — asking an image model to redraw a character's animation frames, which wrecks proportions, palette and frame-to-frame consistency — and through the method that works: cut the frames out of the original art, scale them by whole-number nearest neighbour, composite the missing animations algorithmically, then assemble and verify the atlas.

Along the way it covers the parts that are easy to get wrong: chroma-keying the background without eating the character's own colours, harvesting a run cycle that loops without a hitch, anchoring the sprite to its feet so it stops jittering, choosing which original frames are the wave and which are the failure, keeping projectiles clipped to their cell, and assembling the sixteen gaze poses without severed necks.

## Install

A skill is a directory containing `SKILL.md` plus whatever it references. Copy this one into whichever skills directory your agent reads:

```sh
git clone https://github.com/dncore/retro-codex-pets /tmp/retro-codex-pets

# Gemini CLI
cp -R /tmp/retro-codex-pets/skills/sprite-to-codex-pet ~/.gemini/config/skills/

# Claude Code
cp -R /tmp/retro-codex-pets/skills/sprite-to-codex-pet ~/.claude/skills/

# per project instead of per user, for either
cp -R /tmp/retro-codex-pets/skills/sprite-to-codex-pet .claude/skills/
```

Then give the agent a sprite sheet and ask for a Codex pet. Any agent that supports the `SKILL.md` convention can read this one; only the directory it goes in differs.

## What is in here

| Path | What it is |
|---|---|
| `SKILL.md` | The skill itself: the spec, the eight-step workflow, the anchoring rules, the quality gate |
| `references/codex_v2_pet_spec.md` | The v2 atlas geometry and the frame-count matrix for all eleven rows |
| `references/common_pitfalls_and_fixes.md` | Sixteen documented failure modes with the fix for each — jitter, shearing, clipping, loop cadence, chroma residue, severed necks, blown-out glow |
| `scripts/pet_doctor.py` | The main quality gate: geometry, transparent-pixel residue, unused columns, edge truncation, centreline jitter, loop cadence, anatomical tears |
| `scripts/chroma_cleaner.py` | Background removal that protects the character's internal palette and zeroes the RGB under transparent pixels |
| `scripts/check_pet.py` | Quick atlas check: dimensions, unused columns, alpha residue, centreline stability |
| `scripts/test_loop_generator.py` | Renders candidate frame sequences to a GIF so you can look at the loop, the seam and the baseline |

Requires Python 3 with Pillow and NumPy:

```sh
python3 -m pip install pillow numpy
python3 scripts/pet_doctor.py path/to/spritesheet.webp
```

## One known limitation

`pet_doctor.py` measures head drift in the running rows by looking for skin-coloured pixels (`r - g >= 25`), which is what tells skin from gold trim. On characters whose armour is gold or white that mask is unstable: when a pose hides most of the face, the detected centroid moves even though the head did not, and a frame with 27 detected skin pixels against 63 in its neighbours can be reported as a 14 px drift.

Measured across the four pets in this repository, the same running rows come out at 1 px, 8 px and 13 px when the drift is measured instead as the bounding-box centre of the character's helmet band, while the skin-based number disagrees with those on two of the four pets in both directions — it passes a row that drifts 13 px and fails one that drifts 8 px. Treat its head-drift verdict as a hint to go and look at the frames, not as a verdict, and prefer a silhouette landmark over a colour mask when the character's palette is close to skin tones.

## Rights

The skill is code and documentation, covered by this repository's MIT [LICENSE](../../LICENSE) — see [Credits and rights](../../README.md#credits-and-rights) for the artwork. Nothing in the skill grants any right to the sprites you feed it: if you convert a commercial game's art, that art still belongs to whoever made it.
