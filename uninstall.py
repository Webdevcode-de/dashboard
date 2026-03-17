import os
import sys
import shutil
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
import winreg

PROGRAM_FILES = os.environ.get("ProgramFiles", "C:\\Program Files")
INSTALL_FOLDER = os.path.join(PROGRAM_FILES, "ScreenOverlayApp")
USER_CONFIG_FOLDER = os.path.join(os.path.expanduser("~"), ".screenapp")
APP_NAME_MAIN = "Screen Overlay App"
APP_NAME_CONFIG = "Overlay Config"
EXE_FILES = ["screen.exe", "configurator.exe", "uninstall.exe"]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def remove_registry_entries():
    for app_name in [APP_NAME_MAIN, APP_NAME_CONFIG]:
        try:
            key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}"
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Failed to remove registry entry {app_name}: {e}")

def remove_startup_shortcut():
    try:
        startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        shortcut = os.path.join(startup, f"{APP_NAME_MAIN}.lnk")
        if os.path.exists(shortcut):
            os.remove(shortcut)
    except Exception as e:
        print("Failed to remove startup shortcut:", e)

def main():
    app = QApplication(sys.argv)
    reply = QMessageBox.question(None, "Uninstall", 
                                 f"Are you sure you want to uninstall {APP_NAME_MAIN} and Overlay Config?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply != QMessageBox.StandardButton.Yes:
        sys.exit(0)

    remove_startup_shortcut()

    # Remove EXEs except uninstall.exe (we delete it via batch)
    for exe in EXE_FILES:
        path = os.path.join(INSTALL_FOLDER, exe)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Failed to remove {path}: {e}")

    # Remove user config folder
    if os.path.exists(USER_CONFIG_FOLDER):
        try:
            shutil.rmtree(USER_CONFIG_FOLDER)
        except Exception as e:
            print("Failed to remove user config:", e)

    # Remove registry entries
    remove_registry_entries()

    # Delete uninstall.exe and install folder silently via batch
    batch_file = os.path.join(os.environ["TEMP"], "del_uninstall.bat")
    with open(batch_file, "w") as f:
        f.write(f"""@echo off
ping 127.0.0.1 -n 2 > nul
rmdir /s /q "{INSTALL_FOLDER}"
del /f /q "%~f0"
""")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f'/c "{batch_file}"', None, 0)

    QMessageBox.information(None, "Uninstall", "Uninstallation initiated. Files will be removed shortly.")
    sys.exit(0)

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)
        sys.exit(0)
    main()