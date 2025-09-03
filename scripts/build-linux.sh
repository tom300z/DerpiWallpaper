#!/usr/bin/env bash
set -xeuo pipefail

# Build DerpiWallpaper for Linux using Nuitka

version=$(poetry version -s)

mkdir -p data
printf "%s" "$version" > data/version.txt

# Fail if version file missing/empty or mismatched
if [[ ! -s data/version.txt ]]; then
  echo "data/version.txt is missing or empty" >&2
  exit 1
fi
if ! grep -Fxq "$version" data/version.txt; then
  echo "data/version.txt content does not match $version" >&2
  exit 1
fi

mkdir -p build
deactivate || true
poetry install
source .venv/bin/activate
python -m nuitka \
  ./derpiwallpaper/__main__.py \
  --onefile \
  --enable-plugin=pyside6 \
  --windows-console-mode=disable \
  --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" \
  --product-name=DerpiWallpaper \
  --product-version="$version" \
  --output-filename="DerpiWallpaper" \
  --output-dir=build \
  --linux-icon="data/derpiwallpaper.png" \
  --include-data-files="data/*=data/" \
  --assume-yes-for-downloads
