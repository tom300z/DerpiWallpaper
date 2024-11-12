### Set up the development environment


### Building the Standalone executable:
#### For windows using Powershell
```powershell
nuitka .\derpiwallpaper\__main__.py --msvc=latest --onefile --enable-plugin=pyside6 --windows-console-mode=disable --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" --product-name=DerpiWallpaper --product-version=$((poetry version).split()[1]) --output-filename="DerpiWallpaper.exe" --windows-icon-from-ico="data\derpibooru.ico" --include-data-files="data/*=data/"
```