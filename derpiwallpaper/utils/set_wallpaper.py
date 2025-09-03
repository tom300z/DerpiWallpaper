import ctypes
import platform
import re
import subprocess
from pathlib import Path

from derpiwallpaper.config import CONFIG
from derpiwallpaper.utils import find_executables

class WallpaperSetError(RuntimeError):
    pass

def set_wallpaper(image_path: str | Path):
    """
    Sets the desktop wallpaper across platforms.

    Args:
        image_path (Path): The path to the image file.
    """
    system = platform.system()

    if system == "Windows":
        # Windows: Use ctypes to set the wallpaper
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 0)

    elif system == "Darwin":  # macOS
        # macOS: Use AppleScript to set the wallpaper
        script = f'''
        tell application "System Events"
            set desktopCount to count of desktops
            repeat with desktopNumber from 1 to desktopCount
                tell desktop desktopNumber
                    set picture to "{image_path}"
                end tell
            end repeat
        end tell
        '''
        subprocess.run(["osascript", "-e", script], check=True)

    elif system == "Linux":
        # Linux: Try common desktop environments (GNOME, KDE, XFCE)
        try:
            # GNOME
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{image_path}"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        try:
            # KDE Plasma
            qdbus_pattern = re.compile(r"^qdbus(-qt)?\d*$")
            qdbus_executable = next(find_executables(qdbus_pattern), None)

            if not qdbus_executable:
                raise WallpaperSetError("Failed to find qdbus executable to set KDE wallpaper.")

            script = f'''
            var allDesktops = desktops();
            for (i=0; i<allDesktops.length; i++) {{
                d = allDesktops[i];
                d.wallpaperPlugin = "org.kde.image";
                d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                d.writeConfig("Image", "file://{image_path}");
            }}
            '''

            subprocess.run([qdbus_executable, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError, WallpaperSetError):
            pass
        try:
            # XFCE
            subprocess.run(["xfconf-query", "--channel", "xfce4-desktop", "--property", "/backdrop/screen0/monitor0/image-path", "--set", str(image_path)], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    else:
        print("Unsupported operating system for setting wallpaper.")
        return

    CONFIG.current_wallpaper_path = str(image_path)
