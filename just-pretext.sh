#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO=$1
DIR="$SCRIPT_DIR/$2"

rm -rf "$DIR"
mkdir -p "$DIR"

cd "$REPO"
git pull
cd pretext

"$SCRIPT_DIR"/list_files.py main.ptx | while read -r f; do
    cp --parents "$f" "$DIR";
done

cp main.ptx "$DIR"
