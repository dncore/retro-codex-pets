English | [简体中文](README.zh-CN.md)

# Retro Codex Pets

Four hand-drawn pixel-art pets for the Codex CLI: two androids from *The Ninja Warriors* and two of X's armors from *Mega Man X4*. Every pet is a complete V2 package — idle, running both ways, waving, jumping, failing, waiting, working, reviewing, and all sixteen gaze poses — so it reacts to what the agent is doing instead of just standing there.

Each preview below is the real pet, animated with the per-frame timings from the table further down.

## Kunoichi

![Kunoichi: idle, running right, running left, waving, jumping, waiting, failed, working, review, and the gaze sweep](previews/nw-kunoichi.gif)

Crimson armored android with twin kunai. `nw-kunoichi` — *The Ninja Warriors*

## Ninja

![Ninja: idle, running right, running left, waving, jumping, waiting, failed, working, review, and the gaze sweep](previews/nw-ninja.gif)

Heavy steel android with extendable forearm blades. `nw-ninja` — *The Ninja Warriors*

## X (Fourth Armor)

![X in the Fourth Armor: idle, running right, running left, waving, jumping, waiting, failed, working, review, and the gaze sweep](previews/x4-fourth-armor.gif)

White-and-gold armor with the Plasma Buster and hover boots. `x4-fourth-armor` — *Mega Man X4*

## X (Ultimate Armor)

![X in the Ultimate Armor: idle, running right, running left, waving, jumping, waiting, failed, working, review, and the gaze sweep](previews/x4-ultimate-armor.gif)

Violet armor with the golden wing crest and the Nova Strike. `x4-ultimate-armor` — *Mega Man X4*

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/dncore/retro-codex-pets/main/install.sh | bash
```

That copies all four pets into `$CODEX_HOME/pets` (`~/.codex/pets` by default). Then open Codex, choose your pet under **Settings -> Appearance -> Pets**, and type `/pet` to bring it out.

Install only some of them, or run from a checkout:

```sh
# named pets only
curl -fsSL https://raw.githubusercontent.com/dncore/retro-codex-pets/main/install.sh | bash -s nw-kunoichi x4-ultimate-armor

# list the ids, or see the options
curl -fsSL https://raw.githubusercontent.com/dncore/retro-codex-pets/main/install.sh | bash -s -- --list

# from a clone: copies from the checkout instead of downloading
git clone https://github.com/dncore/retro-codex-pets && cd retro-codex-pets && ./install.sh
```

`CODEX_HOME` picks the Codex data directory, and `PET_REF` picks a branch or tag to download from:

```sh
CODEX_HOME=/tmp/codex-test PET_REF=v1.0.0 ./install.sh
```

The installer downloads into a staging directory and swaps it into place only once both files have arrived, so a dropped connection cannot leave you with half a pet. To remove one:

```sh
rm -rf "${CODEX_HOME:-$HOME/.codex}/pets/nw-ninja"
```

Installing by hand is two files per pet: copy `pets/<id>/pet.json` and `pets/<id>/spritesheet.webp` into `~/.codex/pets/<id>/`. Codex's own documentation for the feature is at [developers.openai.com/codex/app/settings#codex-pets](https://developers.openai.com/codex/app/settings#codex-pets).

## What's in a pet

A pet package is a folder named after its id, holding a `pet.json` manifest and one spritesheet. These pets are all **sprite version 2** (V2), the atlas format that adds the gaze poses.

```json
{
  "id": "nw-kunoichi",
  "displayName": "Kunoichi",
  "description": "Kunoichi (クノイチ) - agile female ninja android from The Ninja Warriors, sleek crimson armor with dual kunai blades and deadly acrobatic combat.",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

The spritesheets are `1536x2288` WebP, losslessly encoded, 28-40 KB each — small enough that shipping them costs less than a screenshot. Each is an 8-column by 11-row grid of `192x208` cells:

| Row | Track | Frames | Per-frame duration | What it means |
|----:|-------|-------:|--------------------|---------------|
| 0 | idle | 6 | 280, 110, 110, 140, 140, 320 ms | resting breath |
| 1 | running-right | 8 | 120 ms, last frame 220 ms | travelling right |
| 2 | running-left | 8 | 120 ms, last frame 220 ms | travelling left |
| 3 | waving | 4 | 140 ms, last frame 280 ms | hello |
| 4 | jumping | 5 | 140 ms, last frame 280 ms | launch and land |
| 5 | failed | 8 | 140 ms, last frame 240 ms | something broke |
| 6 | waiting | 6 | 150 ms, last frame 260 ms | blocked on you |
| 7 | running | 6 | 120 ms, last frame 220 ms | a task is in progress |
| 8 | review | 6 | 150 ms, last frame 280 ms | inspecting finished work |
| 9-10 | look | 8 + 8 | not timed | sixteen gaze poses, 22.5° apart clockwise from straight up |

A few details that matter if you draw your own:

- **Cells a row does not use are never played.** Leftover art in them is harmless; the validator in [agent-pet-runtime](https://github.com/dncore/agent-pet-runtime) reports it as a warning, not an error. All four pets here carry one such cell, row 0 column 6 — a spare idle frame that nothing can reach.
- **The gaze rows are poses, not an animation.** Codex picks one by pointer angle, which is why the preview sweeps through all sixteen for you.
- **The idle timings are the authored ones.** Codex's own table multiplies those six durations by six and stretches the breath into something very slow; the preview GIFs use the authored timings.
- **Waving, jumping, failed and review are moments.** They play their row a few times and then settle back into idle. Waiting and the two running rows are conditions, and loop for as long as the condition holds.

## Rebuilding the previews

```sh
python3 -m pip install pillow numpy
python3 tools/make_previews.py                      # writes previews/<id>.gif
python3 tools/make_previews.py --scale 3 --background paper
```

The generator reads each package's own manifest and spritesheet, plays the tracks with the durations above, and composites a 2x nearest-neighbour card on a checkerboard so the transparency is visible. Options: `--pets-dir`, `--out-dir`, `--pets`, `--scale`, `--background {checker,paper,ink}`.

## Credits

The sprites are fan art, drawn by hand for these pets. *The Ninja Warriors* and its androids are Taito's; *Mega Man X4*, X, and the Fourth and Ultimate Armors are Capcom's. Nothing here is official, endorsed, or licensed by either company, and the art is shared for personal, non-commercial use.

## License

The scripts and manifests are MIT — see [LICENSE](LICENSE). The character designs belong to their owners, as noted above.
