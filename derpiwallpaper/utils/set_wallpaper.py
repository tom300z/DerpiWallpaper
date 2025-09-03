import ctypes
import os
import platform
import re
import subprocess
from pathlib import Path

from derpiwallpaper.config import CONFIG
from derpiwallpaper.utils import find_executables

class WallpaperSetError(RuntimeError):
    pass

def _detect_linux_desktop_env() -> str | None:
    """Best-effort detection of the current Linux desktop environment.

    Returns one of: "gnome", "kde", "xfce" or None if unknown.

    Detection uses common environment variables first, then falls back
    to checking for well-known processes. Works for both X11 and Wayland.
    """
    xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()

    candidates = " ".join([xdg, session])

    if any(k in candidates for k in ["gnome", "ubuntu:gnome", "unity"]):
        return "gnome"
    if any(k in candidates for k in ["kde", "plasma"]):
        return "kde"
    if any(k in candidates for k in ["xfce", "xfce4"]):
        return "xfce"

    # Extra env hints
    if os.environ.get("KDE_FULL_SESSION", "").lower() in ("1", "true", "yes"):  # noqa: PLC1901
        return "kde"
    if os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        return "gnome"

    # Process fallbacks
    try:
        ps = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True)
        if ps.returncode == 0:
            procs = ps.stdout.lower()
            if "gnome-shell" in procs:
                return "gnome"
            if "plasmashell" in procs:
                return "kde"
            if "xfce4-session" in procs:
                return "xfce"
    except Exception:
        # If ps is unavailable or fails, ignore and return None.
        pass

    return None

def _run_or_raise(cmd: list[str]):
    """Run a command; on nonzero exit raise WallpaperSetError with stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Per requirement, include stdout in the error. It may be empty.
        raise WallpaperSetError(result.stdout.strip())
    return result

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
        # Linux: Detect the active desktop environment and only run its code.
        de = _detect_linux_desktop_env()
        if de is None:
            raise WallpaperSetError("Unable to detect Linux desktop environment (GNOME/KDE/XFCE).")

        if de == "gnome":
            _run_or_raise(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{image_path}"])

        elif de == "kde":
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

            _run_or_raise([str(qdbus_executable), "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script])

        elif de == "xfce":
            _run_or_raise(["xfconf-query", "--channel", "xfce4-desktop", "--property", "/backdrop/screen0/monitor0/image-path", "--set", str(image_path)])
        else:
            # Safety net, though we should only reach here for supported DEs.
            raise WallpaperSetError(f"Unsupported Linux desktop environment: {de}")
    else:
        raise WallpaperSetError("Unsupported operating system for setting wallpaper.")

    CONFIG.current_wallpaper_path = str(image_path)
