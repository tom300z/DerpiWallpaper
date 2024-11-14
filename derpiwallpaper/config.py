from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir

from derpiwallpaper.utils import get_user_images_folder

class DerpiWallpaperConfig:
    # Default configuration settings as class attributes
    derpibooru_json_api_key = ""  # Defaults to public api
    derpibooru_json_api_url = "https://derpibooru.org/api/v1/json/"
    search_string: str = "wallpaper,score.gt:200,safe,-anthro,-comic,-human"
    enable_auto_refresh: bool = False
    minimize_to_tray: bool = True
    auto_refresh_interval_seconds: int = 360
    current_wallpaper_path: str = ""
    wallpapers_to_keep: int = 100
    wallpaper_folder: Path = get_user_images_folder() / "DerpiWallpaper"

    @property
    def appdir(self) -> Path:
        return Path(user_config_dir(appname="DerpiWallpaper", appauthor=False))

    def __init__(self):
        # Define the config path using appdirs
        config_dir = self.appdir
        config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = config_dir / "config.ini"

        # Load or initialize the config file
        self.config = ConfigParser()
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            self.config["DerpiWallpaper"] = {}

        # Load or initialize attributes from the file
        for attr_name, default_value in self._get_configurable_attrs().items():
            # Load from config file if present, otherwise set default
            if attr_name in self.config["DerpiWallpaper"]:
                attr_type = type(default_value)
                loaded_value = self.config["DerpiWallpaper"][attr_name]
                # Convert the loaded string to the attribute's type
                if attr_type == bool:
                    value = False if loaded_value.upper() in ["FALSE", "NO", "N", 0] else True
                else:
                    value = attr_type(loaded_value)
                setattr(self, attr_name, value)
            else:
                setattr(self, attr_name, default_value)  # Set the default if missing in file

        # Save to ensure any missing defaults are written to the file
        self._save()
        print(f'Loaded configuration from "{self.config_path}"')

    def __setattr__(self, key, value):
        # Only process configurable attributes (i.e., those not starting with '_')
        if key in self._get_configurable_attrs():
            # Update the config parser and write to file
            if self.config.get("DerpiWallpaper", key, fallback=None) != str(value):
                self.config["DerpiWallpaper"][key] = str(value)
                self._save()
        # Call the superclass's setattr to actually set the attribute
        super().__setattr__(key, value)

    def _get_configurable_attrs(self):
        """Return a dictionary of configurable attributes with their default values."""
        return {attr: getattr(self, attr) for attr in self.__class__.__annotations__ if not attr.startswith("_")}

    def _save(self):
        """Writes the current configuration to the config file."""
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)

# Create config instance
CONFIG = DerpiWallpaperConfig()
CLEANUP_INTERVAL = 60  # Intentionally hardcoded to avoid accidental cleanup

# Create wallpaper folder
CONFIG.wallpaper_folder.mkdir(parents=True, exist_ok = True)
