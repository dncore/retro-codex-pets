English | [简体中文](README.zh-CN.md)

# Retro Codex Pets

Four pixel-art pets for the Codex CLI, built from the original console sprite art of the games they depict: two androids from *The Ninja Warriors* and two of X's armors from *Mega Man X4*. Every pet is a complete V2 package — idle, running both ways, waving, jumping, failing, waiting, working, reviewing, and all sixteen gaze poses — so it reacts to what the agent is doing instead of just standing there.

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
CODEX_HOME=/tmp/codex-test ./install.sh      # install somewhere else
PET_REF=some-branch ./install.sh             # or: a branch, or a tag
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

Every preview records the SHA-256 of the atlas it was built from in a GIF comment, and CI compares that against the atlas actually shipping. A preview that has fallen behind its spritesheet fails the check instead of being published.

## Credits and rights

The sprite art in these pets comes from the original console sprite art of the games they depict: *The Ninja Warriors* (Taito) and *Mega Man X4* (Capcom). The characters, the designs, the original sprites, and the names belong to their owners. No original artwork is claimed here, and no ownership of any of it is asserted.

This is a personal, non-commercial fan project:

- **No profit of any kind.** Nothing here is sold, licensed, sponsored, or monetized — no ads, no paid tiers, no donations, no affiliate links, no revenue.
- **No affiliation.** This is not authorized by, endorsed by, or connected to Taito, Capcom, or OpenAI.
- **Non-commercial use only.** The packages are published so that other people can use the same pets with their own Codex install. They are not licensed for commercial use or for inclusion in anything sold.
- **Removal on request.** If you hold the rights to this material and want it taken down, open an issue and it will be removed.

The games themselves are published and re-released by their rights holders, and that is the only place these characters are officially available.

## License

The scripts and manifests are MIT — see [LICENSE](LICENSE). That grant covers the code in this repository, not the artwork; the characters and the sprites they are built from belong to their owners, as set out above.
