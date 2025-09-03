Param(
  [switch]$NoVersionWrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Build DerpiWallpaper for Windows using Nuitka

$version = (poetry version -s)

New-Item -ItemType Directory -Force -Path data | Out-Null
if (-not $NoVersionWrite) {
  Set-Content -Path data\version.txt -Value $version -NoNewline -Encoding ascii
}

# Fail if version file missing/empty or mismatched
if (!(Test-Path data\version.txt) -or (Get-Item data\version.txt).Length -eq 0) {
  throw 'data/version.txt is missing or empty'
}
$content = Get-Content data\version.txt -Raw
if ($content -ne $version) {
  throw "data/version.txt content does not match $version"
}

New-Item -ItemType Directory -Force -Path build | Out-Null

poetry run nuitka \
  .\derpiwallpaper\__main__.py \
  --msvc=latest \
  --onefile \
  --enable-plugin=pyside6 \
  --windows-console-mode=disable \
  --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" \
  --product-name=DerpiWallpaper \
  --product-version=$version \
  --output-filename="DerpiWallpaper.exe" \
  --output-dir build \
  --windows-icon-from-ico="data\derpiwallpaper.ico" \
  --include-data-files="data/*=data/"

