

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QCloseEvent, QIcon, QAction
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QWidget, QGroupBox, QCheckBox, QSpinBox, QSystemTrayIcon, QMenu, QMainWindow, QApplication, QTextBrowser

from derpiwallpaper.autostart import is_run_on_startup, run_on_startup
from derpiwallpaper.config import CONFIG
from derpiwallpaper.workers import WorkerManager

ICON_PATH = Path(__file__).parent.parent / "data" / "derpiwallpaper.ico"


class DerpiWallpaperUI(QWidget):
    workers: WorkerManager
    tray_icon: QSystemTrayIcon | None = None
    def __init__(self, workers: WorkerManager) -> None:
        super().__init__()
        self.workers = workers
        self.icon = QIcon(str(ICON_PATH))

        layout = QGridLayout(self)
        layout.addWidget(self.create_search_options_widget(), 0, 0, 1, 4)
        layout.addWidget(self.create_program_options_widget(), 1, 0, 1, 4)
        layout.setRowStretch(5, 1)
        layout.addLayout(self.create_update_widgets(), 6, 0, 1, 4)

        #envvars = QTextBrowser()
        #envvars.setText('\n'.join(f'{k} = {v}' for k, v in os.environ.items()))
        #layout.addWidget(envvars, 7, 0, 1, 4)

        self.resize(600, 200)
        self.setWindowTitle("DerpiWallpaper")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.configure_minimize_to_tray(CONFIG.minimize_to_tray)

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
            refresh_action.triggered.connect(self.update_wp)


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

        search_input = QLineEdit(CONFIG.search_string)
        search_input.setPlaceholderText("Enter derpibooru.org search string...")
        search_input.setToolTip("derpibooru.org search string")
        search_input.textChanged.connect(lambda search_string: setattr(CONFIG, "search_string", search_string))

        search_results = QLabel("0 images match your search.")
        def update_results_label():
            if not self.workers.search.current_error_msg:
                style = ""
                results_text = f"{self.workers.search.current_result_count} images match your search."
            else:
                style = "color: red"
                results_text = f"Invalid search string: {self.workers.search.current_error_msg}"
            search_results.setText(results_text)
            search_results.setStyleSheet(style)
        self.workers.search.update_ui.connect(update_results_label)
        search_description = QLabel("See <a href=\"https://derpibooru.org/pages/search_syntax\">Search Syntax</a> for instructions on how to build your search string.")
        search_description.setOpenExternalLinks(True)

        # Layout
        widget = QGroupBox("Search")
        layout = QGridLayout(widget)
        layout.addWidget(search_label, 0, 0, 1, 1)
        layout.addWidget(search_input, 1, 0, 1, 1)
        layout.addWidget(search_results, 2, 0, 1, 1)
        layout.addWidget(search_description, 3, 0, 1, 1)
        return widget

    def create_program_options_widget(self):
        autostart_checkbox = QCheckBox("Run on boot (minimized)")
        autostart_checkbox.setChecked(is_run_on_startup())
        if autostart_checkbox.isChecked(): run_on_startup(True)  # Update the autostart entry to the current binary
        def toggle_auto_start(enabled: bool):
            run_on_startup(enabled)
        autostart_checkbox.toggled.connect(toggle_auto_start)

        minimize_to_tray_checkbox = QCheckBox("Minimize to tray")
        minimize_to_tray_checkbox.setChecked(CONFIG.minimize_to_tray)
        def toggle_minimize_to_tray(enabled: bool):
            CONFIG.minimize_to_tray = enabled
            self.configure_minimize_to_tray(CONFIG.minimize_to_tray)
        minimize_to_tray_checkbox.toggled.connect(toggle_minimize_to_tray)

        auto_refresh_checkbox = QCheckBox("Auto refresh wallpaper")
        auto_refresh_checkbox.setChecked(CONFIG.enable_auto_refresh)
        def toggle_auto_refresh(enabled: bool):
            CONFIG.enable_auto_refresh = enabled
            self.workers.wp_updater.schedule_refresh(datetime.now() if enabled else None)
        auto_refresh_checkbox.toggled.connect(toggle_auto_refresh)

        auto_refresh_interval_label = QLabel("Every:")
        auto_refresh_interval = QSpinBox()
        auto_refresh_interval.setMinimum(1)
        auto_refresh_interval.setMaximum(600)
        auto_refresh_interval.setValue(int(CONFIG.auto_refresh_interval_seconds/60))
        auto_refresh_interval.setSuffix(" min")
        def set_auto_refresh_interval(interval_mins: int):
            CONFIG.auto_refresh_interval_seconds = interval_mins*60
            self.workers.wp_updater.schedule_refresh(datetime.now())
        auto_refresh_interval.valueChanged.connect(set_auto_refresh_interval)
        auto_refresh_checkbox.toggled.connect(toggle_auto_refresh)

        # Layout
        widget = QGroupBox("Program")
        layout = QGridLayout(widget)
        layout.addWidget(autostart_checkbox,          0, 0, 1, 2)
        layout.addWidget(minimize_to_tray_checkbox,          0, 2, 1, 2)
        layout.addWidget(auto_refresh_checkbox,       1, 0, 1, 2)
        layout.addWidget(auto_refresh_interval_label, 1, 2)
        layout.addWidget(auto_refresh_interval,       1, 3)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(3, 1)

        return widget

    def update_wp(self):
        self.workers.wp_updater.schedule_refresh(datetime.now(), update_ui=False)

    def create_update_widgets(self):
        update_wallpaper_button = QPushButton("Update wallpaper!")
        update_wallpaper_button.released.connect(self.update_wp)

        update_progress_bar = QProgressBar()
        def update_progress_ui():
            """Updates the progress bar and reenables the button."""

            update_progress_bar.setMaximum(self.workers.wp_updater.max_steps)
            update_progress_bar.setValue(self.workers.wp_updater.progress)
            if self.workers.wp_updater.progress >= self.workers.wp_updater.max_steps:
                update_wallpaper_button.setDisabled(False)
                next_refresh_time = self.workers.wp_updater.get_next_refresh_time()
                if next_refresh_time:
                    button_text = f"Update wallpaper! (next auto-refresh at {next_refresh_time.strftime("%H:%M")})"
                else:
                    button_text = "Update wallpaper!"
                update_wallpaper_button.setText(button_text)
            else:
                update_wallpaper_button.setDisabled(True)
                update_wallpaper_button.setText("Updating wallpaper...")
        self.workers.wp_updater.update_ui.connect(update_progress_ui)

        layout = QGridLayout()
        layout.addWidget(update_wallpaper_button, 6, 0, 1, 4)
        layout.addWidget(update_progress_bar, 7, 0, 1, 4)
        return layout