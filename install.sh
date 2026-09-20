#!/usr/bin/env bash
# Install Codex pets from dncore/retro-codex-pets into $CODEX_HOME/pets.
#
#   curl -fsSL https://raw.githubusercontent.com/dncore/retro-codex-pets/main/install.sh | bash
#   bash install.sh nw-ninja x4-fourth-armor      # only these two
#   bash install.sh --list
#
# Run it from a checkout and it copies from that checkout; run it from a pipe
# and it downloads from GitHub. CODEX_HOME picks the Codex data directory
# (default ~/.codex). PET_REF picks the branch or tag to download from.

set -euo pipefail

REPO="dncore/retro-codex-pets"
RAW="https://raw.githubusercontent.com/$REPO/${PET_REF:-main}"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
PETS_DIR="$CODEX_DIR/pets"
KNOWN=(nw-kunoichi nw-ninja x4-fourth-armor x4-ultimate-armor)

usage() {
  cat <<EOF
Install Codex pets into $PETS_DIR

Usage: install.sh [pet ...]        install every pet, or only the ones named
       install.sh --list           print the available pet ids
       install.sh --help           print this message

Available pets: ${KNOWN[*]}
EOF
}

# A checkout next to this script wins over the network, but only when the
# script arrived as a file. Piped in through curl, BASH_SOURCE is unset and the
# working directory belongs to the caller, which is not a source for anything.
SELF="${BASH_SOURCE[0]:-}"
SELF_DIR=""
if [ -n "$SELF" ] && [ -f "$SELF" ]; then
  SELF_DIR="$(cd "$(dirname "$SELF")" && pwd)"
fi
LOCAL_PETS=""
if [ -n "$SELF_DIR" ] && [ -d "$SELF_DIR/pets" ]; then
  LOCAL_PETS="$SELF_DIR/pets"
  SOURCE="local $LOCAL_PETS"
else
  SOURCE="remote $RAW"
fi

wanted=()
# ${@+"$@"} rather than "$@": macOS ships bash 3.2, where an empty "$@" is an
# unbound variable under set -u.
for arg in ${@+"$@"}; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    -l|--list) printf '%s\n' "${KNOWN[@]}"; exit 0 ;;
    -*)
      echo "install.sh: unknown option $arg" >&2
      usage >&2
      exit 2
      ;;
    *) wanted+=("$arg") ;;
  esac
done
[ ${#wanted[@]} -gt 0 ] || wanted=("${KNOWN[@]}")

for id in "${wanted[@]}"; do
  case " ${KNOWN[*]} " in
    *" $id "*) ;;
    *)
      echo "install.sh: unknown pet '$id'" >&2
      usage >&2
      exit 2
      ;;
  esac
done

echo "Installing ${#wanted[@]} pet(s) into $PETS_DIR  (from $SOURCE)"
mkdir -p "$PETS_DIR"

staging=""
cleanup() {
  if [ -n "$staging" ]; then rm -rf "$staging"; fi
}
trap cleanup EXIT

for id in "${wanted[@]}"; do
  dest="$PETS_DIR/$id"
  # Staged outside the pets directory: an abandoned half-package in there
  # would be picked up as a pet.
  staging="$(mktemp -d "${TMPDIR:-/tmp}/retro-codex-pets.XXXXXX")"

  if [ -n "$LOCAL_PETS" ]; then
    cp "$LOCAL_PETS/$id/pet.json" "$LOCAL_PETS/$id/spritesheet.webp" "$staging/"
  else
    curl -fsSL "$RAW/pets/$id/pet.json" -o "$staging/pet.json"
    curl -fsSL "$RAW/pets/$id/spritesheet.webp" -o "$staging/spritesheet.webp"
  fi

  # Swap only once both files are in place, so a failed download cannot
  # replace a working pet with half of one.
  [ -d "$dest" ] && was="replaced" || was="installed"
  rm -rf "$dest"
  mv "$staging" "$dest"
  staging=""
  echo "  $was $id"
done

echo
echo "Open Codex and pick one: Settings -> Appearance -> Pets, or type /pet."
