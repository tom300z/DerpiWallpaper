

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QEvent, SignalInstance, Slot, Signal, QUrl
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QWidget, QGroupBox, QCheckBox, QSpinBox, QSystemTrayIcon, QMenu, QMainWindow, QApplication, QMessageBox
from PySide6.QtGui import QDesktopServices
from derpiwallpaper.autostart import is_run_on_startup, run_on_startup
from derpiwallpaper.config import CONFIG
from derpiwallpaper.workers import WorkerManager, wman

ICON_PATH = Path(__file__).parent.parent / "data" / "derpiwallpaper.ico"

class DerpiWallpaperApp(QApplication):
    start_minimized: bool

    def __init__(self, start_minimized = False) -> None:
        super().__init__()
        self.start_minimized = start_minimized

    @Slot(Exception)
    def exit_with_error_popup(self, error: Exception):
        error_dialog = QMessageBox()
        error_dialog.setWindowIcon(QIcon(str(ICON_PATH)))
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("I just dont know what went wrong...")
        #error_dialog.setText(getattr(error, "message", str(error)))
        error_dialog.setText(str(error))
        error_dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        error_dialog.setInformativeText('Please click "Report Issue" to report this issue on Github.')

        # Add the "Ok" and "Report Issue" buttons
        report_issue_button = error_dialog.addButton("Report Issue", QMessageBox.ButtonRole.ActionRole)

        # Function to open GitHub issue link with prefilled error message
        def open_github_issue():
            issue_url = f"https://github.com/tom300z/DerpiWallpaper/issues/new?body={QUrl.toPercentEncoding(str(error)).toStdString()}"
            QDesktopServices.openUrl(issue_url)

        # Connect the "Report Issue" button to the GitHub function
        report_issue_button.clicked.connect(open_github_issue)

        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.exec()

        self.quit()

    def exec(self) -> int:
        # Start UI widget
        widget = DerpiWallpaperUI()

        if self.start_minimized:
            if not CONFIG.minimize_to_tray:
                widget.showMinimized()
        else:
            widget.show()

        return super().exec()


class DerpiWallpaperUI(QWidget):
    tray_icon: QSystemTrayIcon | None = None
    wman: WorkerManager

    def __init__(self) -> None:
        super().__init__()
        self.icon = QIcon(str(ICON_PATH))
        self.wman = wman()

        layout = QGridLayout(self)
        layout.addWidget(self.create_search_options_widget(), 0, 0, 1, 4)
        layout.addWidget(self.create_program_options_widget(), 1, 0, 1, 4)
        layout.setRowStretch(5, 1)
        layout.addLayout(self.create_update_widget(), 6, 0, 1, 4)

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
            self.wman.wp_updater.schedule_refresh(datetime.now() if enabled else None)
        auto_refresh_checkbox.toggled.connect(toggle_auto_refresh)

        auto_refresh_interval_label = QLabel("Every:")
        auto_refresh_interval = QSpinBox()
        auto_refresh_interval.setMinimum(1)
        auto_refresh_interval.setMaximum(600)
        auto_refresh_interval.setValue(int(CONFIG.auto_refresh_interval_seconds/60))
        auto_refresh_interval.setSuffix(" min")
        def set_auto_refresh_interval(interval_mins: int):
            CONFIG.auto_refresh_interval_seconds = interval_mins*60
            self.wman.wp_updater.schedule_refresh(datetime.now())
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
        self.wman.wp_updater.schedule_refresh(datetime.now(), update_ui=False)

    def create_update_widget(self):
        update_wallpaper_button = QPushButton("Update wallpaper!")
        update_wallpaper_button.released.connect(self.update_wp)
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

        self.wman.wp_updater.update_ui.connect(update_update_widget)
        self.wman.search.update_ui.connect(update_update_widget)

        layout = QGridLayout()
        layout.addWidget(update_wallpaper_button, 0, 0, 1, 4)
        layout.addWidget(update_progress_bar, 1, 0, 1, 4)
        layout.addWidget(update_error_label, 2, 0, 1, 4)
        return layout