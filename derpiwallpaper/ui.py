

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QEvent, SignalInstance, Slot, Signal, QUrl
from PySide6.QtGui import QIcon, QAction, QGuiApplication
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QWidget, QGroupBox, QCheckBox, QSpinBox, QSystemTrayIcon, QMenu, QMainWindow, QApplication, QMessageBox
from PySide6.QtGui import QDesktopServices, QPixmap, QPainter

from derpiwallpaper.autostart import is_run_on_startup, configure_run_on_startup
from derpiwallpaper.config import get_conf, DATA_PATH, PACKAGE_VERSION
from derpiwallpaper.workers import WorkerManager, wman
import traceback
from urllib.parse import quote

ICON_PATH = DATA_PATH / "derpiwallpaper.ico"

class DerpiWallpaperApp(QApplication):
    start_minimized: bool
    refresh_on_start: bool

    def __init__(self, start_minimized = False, refresh_on_start=False) -> None:
        super().__init__()
        self.start_minimized = start_minimized
        self.refresh_on_start = refresh_on_start

    @Slot(Exception)
    def exit_with_error_popup(self, error: Exception):
        # Build error text and attach as expandable details
        error_text = f'{error.__class__.__name__}: {str(error)}'
        try:
            tb_lines = traceback.TracebackException.from_exception(error).format()
            error_text_full = ''.join(tb_lines)
        except Exception:
            error_text_full = 'No traceback available.'

        error_dialog = QMessageBox()
        error_dialog.setWindowIcon(QIcon(str(ICON_PATH)))
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("I just dont know what went wrong...")
        #error_dialog.setText(getattr(error, "message", str(error)))
        error_dialog.setText(error_text)
        error_dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        error_dialog.setInformativeText('Click "Show Details" for traceback. Use "Report Issue" to file on GitHub.')

        error_dialog.setDetailedText(error_text_full)

        # Add the "Ok" and "Report Issue" buttons
        report_issue_button = error_dialog.addButton("Report Issue", QMessageBox.ButtonRole.ActionRole)
        copy_button = error_dialog.addButton("Copy Traceback", QMessageBox.ButtonRole.ActionRole)

        # Function to open GitHub issue link with prefilled error message
        def open_github_issue():
            base = f"https://github.com/tom300z/DerpiWallpaper/issues/new?title={quote(error_text)}&body="

            body_text = f"Version: {PACKAGE_VERSION}"+"\n"+"Error:\n" + error_text_full

            # Limit total URL length to a conservative 2000 chars
            limit = 2000
            allowed = max(0, limit - len(base))

            # Truncate body so that percent-encoded length fits into allowed
            suffix = "\n\n...[truncated]"
            text = body_text
            encoded = quote(text)
            if len(encoded) > allowed:
                # Rough cut then refine to fit
                # Start with a proportional guess to reduce iterations
                approx_ratio = allowed / max(1, len(encoded))
                cut_len = int(len(text) * approx_ratio)
                cut_len = max(0, cut_len - len(suffix))
                text = text[:cut_len] + suffix
                encoded = quote(text)
                # If still too long, trim iteratively
                while len(encoded) > allowed and cut_len > 0:
                    cut_len = max(0, cut_len - max(16, int(cut_len * 0.1)))
                    text = body_text[:cut_len] + suffix
                    encoded = quote(text)

            issue_url = base + encoded
            QDesktopServices.openUrl(QUrl(issue_url))

        # Connect the "Report Issue" button to the GitHub function
        report_issue_button.clicked.connect(open_github_issue)

        # Copy traceback to clipboard
        def copy_error_to_clipboard():
            QGuiApplication.clipboard().setText(error_text_full)
        copy_button.clicked.connect(copy_error_to_clipboard)

        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.exec()

        self.quit()

    def exec(self) -> int:
        # Start UI widget
        widget = DerpiWallpaperUI()

        if self.start_minimized:
            if not get_conf().minimize_to_tray:
                widget.showMinimized()
        else:
            widget.show()

        if self.refresh_on_start:
            widget.refresh_wp()

        return super().exec()


class DerpiWallpaperUI(QWidget):
    tray_icon: QSystemTrayIcon | None = None
    wman: WorkerManager

    def __init__(self) -> None:
        super().__init__()
        self.icon = QIcon(str(ICON_PATH))
        self.wman = wman()

        layout = QGridLayout(self)
        layout.addWidget(self.create_search_options_widget(), 0, 0)
        layout.addWidget(self.create_program_options_widget(), 1, 0)
        layout.addWidget(self.create_recent_wallpapers_widget(), 0, 1, 2, 1)
        layout.setRowStretch(5, 1)
        layout.addLayout(self.create_update_widget(), 6, 0, 1, 2)

        #envvars = QTextBrowser()
        #envvars.setText('\n'.join(f'{k} = {v}' for k, v in os.environ.items()))
        #layout.addWidget(envvars, 7, 0, 1, 4)

        self.resize(600, 200)
        self.setWindowTitle("DerpiWallpaper")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.configure_minimize_to_tray(get_conf().minimize_to_tray)

    def configure_minimize_to_tray(self, enabled: bool):
        if enabled:
            # Set up the tray icon
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.windowIcon())  # Replace with your icon path

            # Set up the context menu for the tray icon
            tray_menu = QMenu()
            restore_action = QAction("Restore", self)
            restore_action.triggered.connect(self.show_and_raise)
            refresh_action = QAction("Refresh wallpaper", self)
            refresh_action.triggered.connect(self.refresh_wp)


            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(QApplication.instance().quit) # type: ignore

            tray_menu.addAction(restore_action)
            tray_menu.addAction(refresh_action)
            tray_menu.addAction(exit_action)

            self.tray_icon.setContextMenu(tray_menu)

            # Connect left-click action
            def on_tray_icon_activated(reason):
                """Handle clicks on the tray icon."""
                if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Left-click
                    self.show_and_raise()
            self.tray_icon.activated.connect(on_tray_icon_activated)

            # Show the tray icon
            self.tray_icon.show()
        else:
            if self.tray_icon:
                self.tray_icon.deleteLater()
                self.tray_icon = None


    def show_and_raise(self):
        """Restore the window and bring it to the front."""
        self.showNormal()
        self.activateWindow()

    def event(self, event):
        """Override to hide the window on minimize."""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.tray_icon:
                self.hide()
                return True
        return super().event(event)

    def create_search_options_widget(self):
        # Search string
        search_label = QLabel("Search string:")

        search_input = QLineEdit(get_conf().search_string)
        search_input.setPlaceholderText("Enter derpibooru.org search string...")
        search_input.setToolTip("derpibooru.org search string")
        search_input.textChanged.connect(lambda search_string: setattr(get_conf(), "search_string", search_string))

        search_results = QLabel("Searching for images...")
        search_description = QLabel("See <a href=\"https://derpibooru.org/pages/search_syntax\">Search Syntax</a> for instructions on how to build your search string.")
        search_description.setOpenExternalLinks(True)

        def update_search_options_widget():
            if self.wman.search.temporary_error:
                style = "color: red"
                results_text = self.wman.search.temporary_error
            else:
                style = "" if self.wman.search.current_result_count else "color: red"
                results_text = f"{self.wman.search.current_result_count} images match your search."

            search_results.setStyleSheet(style)
            search_results.setText(results_text)
        update_search_options_widget()
        self.wman.search.update_ui.connect(update_search_options_widget)

        # Layout
        widget = QGroupBox("Search")
        layout = QGridLayout(widget)
        layout.addWidget(search_label, 0, 0, 1, 1)
        layout.addWidget(search_input, 1, 0, 1, 1)
        layout.addWidget(search_results, 2, 0, 1, 1)
        layout.addWidget(search_description, 3, 0, 1, 1)
        return widget

    def create_program_options_widget(self):
        autostart_checkbox = QCheckBox("Run on login (minimized)")
        autostart_checkbox.setChecked(is_run_on_startup())
        def toggle_auto_start(enabled: bool):
            configure_run_on_startup(
                enable=enabled,
                flags={
                    "--minimized",
                    *({"--refresh-on-start"} if get_conf().enable_refresh_on_login else set())
                }
            )  # Update the autostart entry to the current binary
        if autostart_checkbox.isChecked(): toggle_auto_start(True)
        autostart_checkbox.toggled.connect(toggle_auto_start)

        minimize_to_tray_checkbox = QCheckBox("Minimize to tray")
        minimize_to_tray_checkbox.setChecked(get_conf().minimize_to_tray)
        def toggle_minimize_to_tray(enabled: bool):
            get_conf().minimize_to_tray = enabled
            self.configure_minimize_to_tray(get_conf().minimize_to_tray)
        minimize_to_tray_checkbox.toggled.connect(toggle_minimize_to_tray)

        auto_refresh_checkbox = QCheckBox("Auto refresh wallpaper")
        auto_refresh_checkbox.setChecked(get_conf().enable_auto_refresh)
        def toggle_auto_refresh(enabled: bool):
            get_conf().enable_auto_refresh = enabled
            self.wman.wp_updater.clear_refresh()
        auto_refresh_checkbox.toggled.connect(toggle_auto_refresh)

        auto_refresh_interval_label = QLabel("Every:")
        auto_refresh_interval = QSpinBox()
        auto_refresh_interval.setMinimum(1)
        auto_refresh_interval.setMaximum(600)
        auto_refresh_interval.setValue(int(get_conf().auto_refresh_interval_seconds/60))
        auto_refresh_interval.setSuffix(" min")
        def set_auto_refresh_interval(interval_mins: int):
            get_conf().auto_refresh_interval_seconds = interval_mins*60
        auto_refresh_interval.valueChanged.connect(set_auto_refresh_interval)
        auto_refresh_checkbox.toggled.connect(toggle_auto_refresh)

        refresh_on_login_checkbox = QCheckBox("Refresh wallpaper on login")
        refresh_on_login_checkbox.setChecked(get_conf().enable_refresh_on_login)
        def toggle_refresh_on_login(enabled: bool):
            get_conf().enable_refresh_on_login = enabled
            toggle_auto_start(enabled=is_run_on_startup())
        refresh_on_login_checkbox.toggled.connect(toggle_refresh_on_login)

        # Layout
        widget = QGroupBox("Program")
        layout = QGridLayout(widget)
        layout.addWidget(autostart_checkbox,                 0, 0, 1, 2)
        layout.addWidget(refresh_on_login_checkbox,          0, 2, 1, 2)
        layout.addWidget(auto_refresh_checkbox,              1, 0, 1, 2)
        layout.addWidget(auto_refresh_interval_label,        1, 2)
        layout.addWidget(auto_refresh_interval,              1, 3)
        layout.addWidget(minimize_to_tray_checkbox,          2, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(3, 1)

        return widget

    def create_recent_wallpapers_widget(self):
        wallpapers_to_keep_label = QLabel("Keep last:")
        wallpapers_to_keep = QSpinBox()
        wallpapers_to_keep.setMinimum(1)
        wallpapers_to_keep.setMaximum(999999)
        wallpapers_to_keep.setValue(get_conf().wallpapers_to_keep)
        def set_wallpapers_to_keep(number: int):
            get_conf().wallpapers_to_keep = number
            self.wman.cleanup.schedule_cleanup()
        wallpapers_to_keep.valueChanged.connect(set_wallpapers_to_keep)

        current_wallpaper_label = QLabel("Current wallpaper:")
        current_wallpaper_image = QLabel()
        current_wallpaper_image.setFixedSize(160, 90)
        current_wallpaper_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        def update_current_wallpaper():
            hidpi_factor = QGuiApplication.primaryScreen().devicePixelRatio()
            pixmap = QPixmap(get_conf().current_wallpaper_path).scaled(int(160*hidpi_factor), int(90*hidpi_factor), Qt.AspectRatioMode.KeepAspectRatio)
            pixmap.setDevicePixelRatio(hidpi_factor)
            current_wallpaper_image.setPixmap(pixmap)
        update_current_wallpaper()
        self.wman.wp_updater.update_ui.connect(update_current_wallpaper)

        open_wallpaper_folder_button = QPushButton("Open wallpaper folder")
        open_wallpaper_folder_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(get_conf().wallpaper_folder))))

        # Layout
        widget = QGroupBox("Recent Wallpapers")
        layout = QGridLayout(widget)

        # Add elements to layout
        layout.addWidget(current_wallpaper_label,     0, 0, 1, 2)
        layout.addWidget(current_wallpaper_image,     1, 0, 1, 2)
        layout.addWidget(open_wallpaper_folder_button, 2, 0, 1, 2)
        layout.addWidget(wallpapers_to_keep_label, 3, 0)
        layout.addWidget(wallpapers_to_keep,       3, 1)

        return widget


    def refresh_wp(self):
        self.wman.wp_updater.schedule_refresh(datetime.now(), update_ui=False)

    def create_update_widget(self):
        update_wallpaper_button = QPushButton("Update wallpaper!")
        update_wallpaper_button.clicked.connect(self.refresh_wp)
        update_wallpaper_button.setMinimumHeight(update_wallpaper_button.fontMetrics().lineSpacing() * 2 + 8)
        update_progress_bar = QProgressBar()
        update_progress_bar.setMaximum(self.wman.wp_updater.max_steps)
        update_error_label = QLabel("blub")
        update_error_label.setStyleSheet("color: red")
        update_error_label.hide()


        def update_update_widget():
            """Updates the progress bar and reenables the button."""

            update_progress_bar.setValue(self.wman.wp_updater.progress)

            # Update Button
            if not self.wman.search.current_result_count:
                update_wallpaper_button.setDisabled(True)
                update_wallpaper_button.setText("No wallpapers found.")
            elif self.wman.wp_updater.progress < self.wman.wp_updater.max_steps:
                update_wallpaper_button.setDisabled(True)
                update_wallpaper_button.setText("Updating wallpaper...")
            else:
                update_wallpaper_button.setDisabled(False)
                next_refresh_time = self.wman.wp_updater.get_next_refresh_time()
                if next_refresh_time:
                    button_text = f"Update wallpaper! (next refresh at {next_refresh_time.strftime("%H:%M")})"
                else:
                    button_text = "Update wallpaper!"
                update_wallpaper_button.setText(button_text)

            # Update Error label
            temp_err = self.wman.wp_updater.temporary_error
            if temp_err:
                update_error_label.show()
                update_error_label.setText(temp_err)
            else:
                update_error_label.hide()
        update_update_widget()
        self.wman.wp_updater.update_ui.connect(update_update_widget)
        self.wman.search.update_ui.connect(update_update_widget)

        layout = QGridLayout()
        layout.addWidget(update_wallpaper_button, 0, 0, 1, 4)
        layout.addWidget(update_progress_bar, 1, 0, 1, 4)
        layout.addWidget(update_error_label, 2, 0, 1, 4)
        return layout
