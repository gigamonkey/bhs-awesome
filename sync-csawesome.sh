#!/usr/bin/env bash

set -euo pipefail

CSAWESOME_ROOT=~/Runestone/books/CSAwesome2

(cd "$CSAWESOME_ROOT" && git pull)

rsync --recursive --delete "$CSAWESOME_ROOT/pretext/" ./csawesome/
