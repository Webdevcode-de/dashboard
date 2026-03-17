import os
import shutil
import winshell
import winreg
import sys

APP_NAME = "Screen Overlay App"
FILES_TO_REMOVE = ["screen.exe", "configurator.exe", "config.json", "uninstall.exe"]

# Determine install folder dynamically
INSTALL_FOLDER = os.path.dirname(sys.executable)

# Remove startup shortcut
startup = winshell.startup()
shortcut_path = os.path.join(startup, f"{APP_NAME}.lnk")
if os.path.exists(shortcut_path):
    os.remove(shortcut_path)

# Remove installed files
for file_name in FILES_TO_REMOVE:
    path = os.path.join(INSTALL_FOLDER, file_name)
    if os.path.exists(path):
        os.remove(path)

# Remove registry uninstall entry
try:
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{}".format(APP_NAME)
    winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
except Exception:
    pass

# Remove install folder if empty
try:
    os.rmdir(INSTALL_FOLDER)
except Exception:
    pass

print("Uninstallation complete.")
input("Press Enter to exit...")