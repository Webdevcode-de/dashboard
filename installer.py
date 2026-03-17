import sys
import os
import shutil
import json
import ctypes
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QCheckBox, QMessageBox
)
import winreg
from win32com.client import Dispatch

# ------------------------ CONFIG ------------------------
DIST_FOLDER = os.path.join(os.path.dirname(__file__), "dist")
PROGRAM_FILES = os.environ.get("ProgramFiles", "C:\\Program Files")
INSTALL_FOLDER = os.path.join(PROGRAM_FILES, "ScreenOverlayApp")
CONFIG_FILE = os.path.join(INSTALL_FOLDER, "config.json")
APP_NAME = "Screen Overlay App"

CONFIG_DEFAULT = {
    "main_window": {"url": "https://example.com", "username": "", "password": ""},
    "overlay_window": {"url": "http://localhost:8000", "width": 610, "height": 600, "x": -10, "y": -100},
    "reload_interval_ms": 5000,
    "config_reload_interval_ms": 2000
}

EXE_FILES = ["configurator.exe", "screen.exe", "uninstall.exe"]

# ------------------------ ADMIN CHECK ------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ------------------------ INSTALL FUNCTION ------------------------
def install_app(run_at_startup, config, dry_run=False):
    if dry_run:
        print("Dry run mode: nothing will be installed.")
        print(f"Would install to {INSTALL_FOLDER}")
        print(f"Config: {json.dumps(config, indent=2)}")
        return True

    os.makedirs(INSTALL_FOLDER, exist_ok=True)

    # Copy executables
    for exe in EXE_FILES:
        src = os.path.join(DIST_FOLDER, exe)
        dst = os.path.join(INSTALL_FOLDER, exe)
        if not os.path.exists(src):
            raise FileNotFoundError(f"{src} not found!")
        shutil.copy2(src, dst)

    # Save config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    # Create startup shortcut if needed
    if run_at_startup:
        try:
            startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup, f"{APP_NAME}.lnk")
            target = os.path.join(INSTALL_FOLDER, "screen.exe")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = INSTALL_FOLDER
            shortcut.save()
        except Exception as e:
            print("Failed to create startup shortcut:", e)

    # Register in Windows installed programs
    register_installed_program()
    return True

# ------------------------ REGISTER IN WIN APPS ------------------------
def register_installed_program():
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{}".format(APP_NAME)
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "uninstall.exe"))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(INSTALL_FOLDER, "screen.exe"))
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "My Company")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
        winreg.CloseKey(key)
    except Exception as e:
        print("Failed to register installed program:", e)

# ------------------------ GUI ------------------------
class Installer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Installer")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Main Window URL & Auth</b>"))
        self.main_url = QLineEdit(CONFIG_DEFAULT["main_window"]["url"])
        self.main_user = QLineEdit(CONFIG_DEFAULT["main_window"]["username"])
        self.main_pass = QLineEdit(CONFIG_DEFAULT["main_window"]["password"])
        self.main_pass.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("URL:")); layout.addWidget(self.main_url)
        layout.addWidget(QLabel("Username:")); layout.addWidget(self.main_user)
        layout.addWidget(QLabel("Password:")); layout.addWidget(self.main_pass)

        layout.addWidget(QLabel("<b>Overlay Settings</b>"))
        self.overlay_url = QLineEdit(CONFIG_DEFAULT["overlay_window"]["url"])
        self.width = QSpinBox(); self.width.setRange(100, 2000); self.width.setValue(CONFIG_DEFAULT["overlay_window"]["width"])
        self.height = QSpinBox(); self.height.setRange(100, 2000); self.height.setValue(CONFIG_DEFAULT["overlay_window"]["height"])
        self.x = QSpinBox(); self.x.setRange(-2000, 2000); self.x.setValue(CONFIG_DEFAULT["overlay_window"]["x"])
        self.y = QSpinBox(); self.y.setRange(-2000, 2000); self.y.setValue(CONFIG_DEFAULT["overlay_window"]["y"])

        layout.addWidget(QLabel("Overlay URL:")); layout.addWidget(self.overlay_url)
        layout.addWidget(QLabel("Width:")); layout.addWidget(self.width)
        layout.addWidget(QLabel("Height:")); layout.addWidget(self.height)
        layout.addWidget(QLabel("X offset:")); layout.addWidget(self.x)
        layout.addWidget(QLabel("Y offset:")); layout.addWidget(self.y)

        self.run_startup = QCheckBox("Run screen.exe at startup")
        layout.addWidget(self.run_startup)

        self.dry_run = QCheckBox("Dry run (no files copied)")
        layout.addWidget(self.dry_run)

        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self.run_install)
        layout.addWidget(self.install_btn)

        self.setLayout(layout)

    def run_install(self):
        config = {
            "main_window": {"url": self.main_url.text(), "username": self.main_user.text(), "password": self.main_pass.text()},
            "overlay_window": {"url": self.overlay_url.text(), "width": self.width.value(), "height": self.height.value(),
                               "x": self.x.value(), "y": self.y.value()},
            "reload_interval_ms": CONFIG_DEFAULT["reload_interval_ms"],
            "config_reload_interval_ms": CONFIG_DEFAULT["config_reload_interval_ms"]
        }
        try:
            install_app(self.run_startup.isChecked(), config, self.dry_run.isChecked())
            QMessageBox.information(self, "Success",
                f"Installed to {INSTALL_FOLDER}" if not self.dry_run.isChecked() else "Dry run complete")
            if not self.dry_run.isChecked():
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ------------------------ RUN ------------------------
if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit(0)

    app = QApplication(sys.argv)
    window = Installer()
    window.show()
    sys.exit(app.exec())