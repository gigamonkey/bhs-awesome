#!/usr/bin/env bash

set -euo pipefail

BHSAWESOME_ROOT=~/Runestone/books/BHSawesome2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$BHSAWESOME_ROOT"
git pull
cd pretext

rm -rf "$SCRIPT_DIR"/just-book
mkdir -p "$SCRIPT_DIR"/just-book

"$SCRIPT_DIR"/list_files.py main.ptx | while read -r f; do
    cp --parents "$f" "$SCRIPT_DIR"/just-book/;
done

cp main.ptx "$SCRIPT_DIR"/just-book/
