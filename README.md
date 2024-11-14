# DerpiWallpaper
<img src="data/derpiwallpaper.ico" alt="app icon" width="100"/>

A tiny Qt application that sets your wallpaper to a random derpibooru.org image matching a search string.

Features:
- No installation required
- Cross platform (tested on Windows, GNOME & KDE)
- Fully customizable via official Derpibooru [search syntax](https://derpibooru.org/pages/search_syntax)
- Configurable Auto refresh
- Save as many recent wallpapers as you want
- Small memory footprint (<50MB)

## Download
See the [Releases](https://github.com/tom300z/DerpiWallpaper/releases) page for downloads.

## How to use
![App Image](docs/app.png)
Download the executable for your OS from the releases page and run it.

The app itself is pretty self explanatory. Just put the binary anywhere on your PC and start it. You can also configure the app to run on boot.

## Development
### Setting up the development environment
1. Install poetry
2. run `poetry install`

### Building the Standalone executable:
#### For windows
```powershell
nuitka .\derpiwallpaper\__main__.py --msvc=latest --onefile --enable-plugin=pyside6 --windows-console-mode=disable --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" --product-name=DerpiWallpaper --product-version=$((poetry version).split()[1]) --output-filename="DerpiWallpaper.exe" --windows-icon-from-ico="data\derpiwallpaper.ico" --include-data-files="data/*=data/"
```
#### For Linux
```bash
sudo apt install python3-dev patchelf gcc
nuitka ./derpiwallpaper/__main__.py --onefile --enable-plugin=pyside6 --windows-console-mode=disable --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" --product-name=DerpiWallpaper --product-version=$(poetry version -s) --output-filename="DerpiWallpaper" --linux-icon="data/derpiwallpaper.png" --include-data-files="data/*=data/"
```
