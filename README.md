# DerpiWallpaper
<img src="data/derpiwallpaper.ico" alt="app icon" width="100"/>

A tiny Qt application to your wallpaper to a random derpibooru image that matches a search string.

Features:
- No installation required
- Fully customizable via official Derpibooru [search syntax](https://derpibooru.org/pages/search_syntax)
- Auto refresh
- Small memory footprint (<50MB)

## How to use
![App Image](docs/app.png)
The app is pretty self explanatory. Just put the binary anywhere on your PC and start it. You can also configure the app to run on boot.

## Development
### Setting up the development environment
1. Install poetry
2. run `poetry install`

### Building the Standalone executable:
#### For windows using Powershell
```powershell
nuitka .\derpiwallpaper\__main__.py --msvc=latest --onefile --enable-plugin=pyside6 --windows-console-mode=disable --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" --product-name=DerpiWallpaper --product-version=$((poetry version).split()[1]) --output-filename="DerpiWallpaper.exe" --windows-icon-from-ico="data\derpibooru.ico" --include-data-files="data/*=data/"
```