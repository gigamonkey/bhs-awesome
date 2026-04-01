#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BHSAWESOME_ROOT=~/Runestone/books/BHSawesome2
LOCAL_DIR="$SCRIPT_DIR"/bhsawesome

rm -rf "$LOCAL_DIR"
mkdir -p "$LOCAL_DIR"

cd "$BHSAWESOME_ROOT"
git pull
cd pretext

"$SCRIPT_DIR"/list_files.py main.ptx | while read -r f; do
    cp --parents "$f" "$LOCAL_DIR";
done

cp main.ptx "$LOCAL_DIR"
