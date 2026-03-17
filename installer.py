import sys
import os
import shutil
import json
import ctypes
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QMessageBox
from win32com.client import Dispatch
import winreg

# Paths
DIST_FOLDER = os.path.join(os.path.dirname(__file__), "dist")
PROGRAM_FILES = os.environ.get("ProgramFiles", "C:\\Program Files")
INSTALL_FOLDER = os.path.join(PROGRAM_FILES, "ScreenOverlayApp")
USER_CONFIG_FOLDER = os.path.join(os.path.expanduser("~"), ".screenapp")

# App names
APP_NAME_MAIN = "Screen Overlay App"
APP_NAME_CONFIG = "Overlay Config"

EXE_FILES = ["screen.exe", "uninstall.exe", "configurator.exe"]

# Default config
CONFIG_DEFAULT = {
    "main_window": {"url": "https://example.com", "username": "", "password": ""},
    "overlay_window": {"url": "http://localhost:8000", "width": 610, "height": 600, "x": -10, "y": -100},
    "reload_interval_ms": 5000,
    "config_reload_interval_ms": 2000
}

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def register_uninstall_entries(install_config_app):
    """Add registry entries for Installed Apps"""
    try:
        # Main app
        key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME_MAIN}"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME_MAIN)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "uninstall.exe"))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "screen.exe"))
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "My Company")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
        winreg.CloseKey(key)

        if install_config_app:
            # Config app entry
            key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME_CONFIG}"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME_CONFIG)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "uninstall.exe"))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "configurator.exe"))
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "My Company")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
            winreg.CloseKey(key)
    except Exception as e:
        print("Registry entry failed:", e)

def create_start_menu_shortcut(app_name, exe_name):
    """Create Start Menu shortcut so Windows Search can find it"""
    try:
        start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        shortcut_path = os.path.join(start_menu, f"{app_name}.lnk")
        target = os.path.join(INSTALL_FOLDER, exe_name)
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = INSTALL_FOLDER
        shortcut.save()
    except Exception as e:
        print(f"Failed to create Start Menu shortcut for {app_name}:", e)

def install_app(run_at_startup, install_config_app, config, dry_run=False):
    if dry_run:
        print("Dry run mode")
        return True

    # Copy EXEs
    os.makedirs(INSTALL_FOLDER, exist_ok=True)
    shutil.copy2(os.path.join(DIST_FOLDER, "screen.exe"), os.path.join(INSTALL_FOLDER, "screen.exe"))
    shutil.copy2(os.path.join(DIST_FOLDER, "uninstall.exe"), os.path.join(INSTALL_FOLDER, "uninstall.exe"))
    if install_config_app:
        shutil.copy2(os.path.join(DIST_FOLDER, "configurator.exe"), os.path.join(INSTALL_FOLDER, "configurator.exe"))

    # Save user config
    os.makedirs(USER_CONFIG_FOLDER, exist_ok=True)
    with open(os.path.join(USER_CONFIG_FOLDER, "config.json"), "w") as f:
        json.dump(config, f, indent=4)

    # Startup shortcut
    if run_at_startup:
        try:
            startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            os.makedirs(startup, exist_ok=True)
            shortcut_path = os.path.join(startup, f"{APP_NAME_MAIN}.lnk")
            target = os.path.join(INSTALL_FOLDER, "screen.exe")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = INSTALL_FOLDER
            shortcut.save()
        except Exception as e:
            print("Failed to create startup shortcut:", e)

    # Start Menu shortcuts for search
    create_start_menu_shortcut(APP_NAME_MAIN, "screen.exe")
    if install_config_app:
        create_start_menu_shortcut(APP_NAME_CONFIG, "configurator.exe")

    # Registry entries for Installed Apps
    register_uninstall_entries(install_config_app)
    return True

# Installer GUI
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QMessageBox

class Installer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Overlay Installer")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.install_config = QCheckBox("Also install Overlay Config (Configurator)")
        layout.addWidget(self.install_config)

        self.run_startup = QCheckBox("Run screen.exe at startup")
        layout.addWidget(self.run_startup)

        self.dry_run = QCheckBox("Dry run (no files copied)")
        layout.addWidget(self.dry_run)

        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self.run_install)
        layout.addWidget(self.install_btn)

        self.setLayout(layout)

    def run_install(self):
        config = CONFIG_DEFAULT
        try:
            install_app(
                self.run_startup.isChecked(),
                self.install_config.isChecked(),
                config,
                self.dry_run.isChecked()
            )
            QMessageBox.information(self, "Success",
                                    "Installed successfully!" if not self.dry_run.isChecked() else "Dry run complete")
            if not self.dry_run.isChecked():
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)
        sys.exit(0)

    app = QApplication(sys.argv)
    window = Installer()
    window.show()
    sys.exit(app.exec())