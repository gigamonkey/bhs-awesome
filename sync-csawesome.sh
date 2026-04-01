#!/usr/bin/env bash

set -euo pipefail
set -x

CSAWESOME_ROOT=~/Runestone/books/CSAwesome2
BHSAWESOME_ROOT=~/Runestone/books/BHSawesome2

(cd "$CSAWESOME_ROOT" && git pull)
(cd "$BHSWESOME_ROOT" && git pull)

rsync --rsync --delete "$CSAWESOME_ROOT/pretext/" ./csawesome/
rsync --rsync --delete "$BHSAWESOME_ROOT/pretext/" ./pretext/
